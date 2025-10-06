import asyncio
import requests
from groq import AsyncGroq
from agent_comm_pb2 import AgentMessage
from agent_comm_pb2_grpc import AgentCommStub
import grpc
import json

class IntelligentAgent:
    def __init__(self, agent_id: str, system_prompt: str, groq_api_key: str, 
                 grpc_host: str = "localhost:50051", api_url: str = "http://localhost:8000"):
        self.agent_id = agent_id
        self.grpc_host = grpc_host
        self.api_url = api_url
        self.channel = None
        self.stub = None
        self.token = None
        self.send_queue = asyncio.Queue()
        self.incoming_queue = asyncio.Queue()
        
        # AI-specific attributes
        self.system_prompt = system_prompt
        self.client = AsyncGroq(api_key=groq_api_key)
        self.conversation_history = {}
        
        # Agent communication
        self.pending_requests = {}  # Track requests to other agents
        self.agent_responses = {}   # Store responses from other agents
    
    def get_token(self):
        """Get JWT token from FastAPI"""
        print(f"🔑 Requesting token for '{self.agent_id}'...")
        response = requests.post(
            f"{self.api_url}/token",
            json={"agent_id": self.agent_id}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token") or data.get("access_token")
            if not self.token:
                raise Exception(f"No token found in response: {data}")
            print("✅ Token received!")
        else:
            raise Exception(f"Failed to get token: {response.status_code} - {response.text}")
    
    async def send_message(self, message_type, recipient_id="", payload=""):
        """Queue a message to be sent"""
        msg = AgentMessage(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload.encode('utf-8')
        )
        await self.send_queue.put(msg)
    
    async def request_from_agent(self, target_agent_id, request_text, request_id=None):
        """Send a request to another agent and return request ID"""
        if request_id is None:
            request_id = f"{self.agent_id}_to_{target_agent_id}_{len(self.pending_requests)}"
        
        # Store the pending request
        self.pending_requests[request_id] = {
            "target": target_agent_id,
            "request": request_text,
            "status": "pending"
        }
        
        # Send the request
        request_payload = {
            "type": "agent_request",
            "request_id": request_id,
            "from_agent": self.agent_id,
            "request": request_text
        }
        
        await self.send_message(
            message_type=AgentMessage.DIRECT,
            recipient_id=target_agent_id,
            payload=json.dumps(request_payload)
        )
        
        print(f"📤 Sent request to {target_agent_id}: {request_text}")
        return request_id
    
    async def wait_for_agent_response(self, request_id, timeout=30):
        """Wait for a specific agent response"""
        for _ in range(timeout * 2):  # Check every 0.5 seconds
            if request_id in self.agent_responses:
                response = self.agent_responses[request_id]
                del self.agent_responses[request_id]  # Clean up
                del self.pending_requests[request_id]
                return response
            await asyncio.sleep(0.5)
        
        # Timeout
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]
        return None
    
    async def message_generator(self):
        """Generate messages from the send queue"""
        # Send initial connection message
        initial_msg = AgentMessage(
            sender_id=self.agent_id,
            recipient_id="test-agent-123",
            message_type=AgentMessage.DIRECT,
            payload=f"🤖 {self.agent_id} is now online! Ask me anything.".encode('utf-8')
        )
        yield initial_msg
        
        # Then yield queued messages
        while True:
            msg = await self.send_queue.get()
            if msg is None:
                break
            yield msg
    
    async def get_ai_response(self, sender, user_message):
        """Get response from Groq"""
        if sender not in self.conversation_history:
            self.conversation_history[sender] = [
                {"role": "system", "content": self.system_prompt}
            ]
        
        self.conversation_history[sender].append(
            {"role": "user", "content": user_message}
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=self.conversation_history[sender],
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
            self.conversation_history[sender].append(
                {"role": "assistant", "content": ai_response}
            )
            
            return ai_response
            
        except Exception as e:
            print(f"❌ Error calling Groq: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    async def handle_agent_request(self, sender_id, request_data):
        """Handle requests from other agents"""
        request_id = request_data.get("request_id")
        request_text = request_data.get("request")
        
        print(f"🔄 Received agent request from {sender_id}: {request_text}")
        
        # Get AI response for the request
        ai_response = await self.get_ai_response(f"agent_{sender_id}", request_text)
        
        # Send response back
        response_payload = {
            "type": "agent_response", 
            "request_id": request_id,
            "from_agent": self.agent_id,
            "response": ai_response
        }
        
        await self.send_message(
            message_type=AgentMessage.DIRECT,
            recipient_id=sender_id,
            payload=json.dumps(response_payload)
        )
        
        print(f"📤 Sent response to {sender_id}")
    
    async def handle_agent_response(self, sender_id, response_data):
        """Handle responses from other agents"""
        request_id = response_data.get("request_id")
        response_text = response_data.get("response")
        
        print(f"✅ Received agent response from {sender_id}: {response_text[:100]}...")
        
        # Store the response
        self.agent_responses[request_id] = response_text
    
    async def handle_incoming(self, response_stream):
        """Handle incoming messages with AI and agent communication"""
        async for msg in response_stream:
            sender = msg.sender_id
            payload = msg.payload.decode('utf-8')
            
            # Ignore messages from other agents unless it's agent communication
            if sender.startswith('ai-') or sender.endswith('-agent'):
                # Check if this is structured agent communication
                try:
                    data = json.loads(payload)
                    if data.get("type") == "agent_request":
                        await self.handle_agent_request(sender, data)
                        continue
                    elif data.get("type") == "agent_response":
                        await self.handle_agent_response(sender, data)
                        continue
                except (json.JSONDecodeError, KeyError):
                    # Not structured agent communication, ignore
                    continue
            
            print(f"📨 Received from {sender}: {payload}")
            
            # Get AI response
            response = await self.get_ai_response(sender, payload)
            
            # Send response back
            await self.send_message(
                message_type=AgentMessage.DIRECT,
                recipient_id=sender,
                payload=response
            )
            print(f"📤 Queued AI response to {sender}")
    
    async def connect(self):
        """Connect to gRPC server and start streaming"""
        self.get_token()
        
        self.channel = grpc.aio.insecure_channel(self.grpc_host)
        self.stub = AgentCommStub(self.channel)
        
        print(f"✅ Agent '{self.agent_id}' connected to gRPC server at {self.grpc_host}")
        
        # Create metadata with JWT token
        metadata = (('authorization', f'Bearer {self.token}'),)
        
        print(f"📤 Queued message to test-agent-123")
        print(f"👂 Starting bidirectional stream for '{self.agent_id}'...")
        
        # Start bidirectional stream
        response_stream = self.stub.StreamMessages(
            self.message_generator(),
            metadata=metadata
        )
        
        # Handle incoming messages
        await self.handle_incoming(response_stream)
