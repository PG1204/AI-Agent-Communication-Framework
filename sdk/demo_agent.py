#!/usr/bin/env python3
"""
Demo agent that communicates via gRPC streaming with JWT authentication
Shows automated agent behavior without LLM
"""

import grpc
import asyncio
import sys
import requests
from agent_comm_pb2 import AgentMessage
from agent_comm_pb2_grpc import AgentCommStub

class DemoAgent:
    def __init__(self, agent_id: str, grpc_host: str = "localhost:50051", api_url: str = "http://localhost:8000"):
        self.agent_id = agent_id
        self.grpc_host = grpc_host
        self.api_url = api_url
        self.channel = None
        self.stub = None
        self.token = None
        self.send_queue = asyncio.Queue()
    
    def get_token(self):
        """Get JWT token from FastAPI"""
        print(f"🔑 Requesting token for '{self.agent_id}'...")
        response = requests.post(
            f"{self.api_url}/token",
            json={"agent_id": self.agent_id}
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print(f"✅ Token received!")
            return True
        else:
            print(f"❌ Failed to get token: {response.text}")
            return False
        
    async def connect(self):
        """Connect to gRPC server with authentication"""
        if not self.get_token():
            raise Exception("Failed to authenticate")
        
        # Create channel with authorization metadata
        self.channel = grpc.aio.insecure_channel(self.grpc_host)
        self.stub = AgentCommStub(self.channel)
        print(f"✅ Agent '{self.agent_id}' connected to gRPC server at {self.grpc_host}")
    
    async def message_generator(self):
        """Generate outgoing messages from queue"""
        while True:
            message = await self.send_queue.get()
            if message is None:  # Shutdown signal
                break
            yield message
    
    async def send_message(self, recipient_id: str, payload: str, message_type: int = 0):
        """Queue a message to be sent"""
        message = AgentMessage(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload.encode('utf-8'),
            # Leave timestamp as 0 or don't set it - database will handle it
            correlation_id=""
        )
        await self.send_queue.put(message)
        print(f"📤 Queued message to {recipient_id if recipient_id else 'ALL'}: '{payload[:50]}...'")
    
    async def handle_message(self, message):
        """Handle incoming message with simple logic"""
        payload = message.payload.decode('utf-8', errors='ignore')
        print(f"\n📨 Received from {message.sender_id}: {payload}")
        
        # Don't respond to our own messages
        if message.sender_id == self.agent_id:
            return
        
        # Demo logic: Auto-respond based on message content
        payload_lower = payload.lower()
        
        if "hello" in payload_lower or "hi" in payload_lower:
            response = f"Hello! I'm {self.agent_id}, an automated agent. How can I help you?"
            await self.send_message(message.sender_id, response)
            
        elif "status" in payload_lower:
            response = f"Status: Online and operational. Current agent ID: {self.agent_id}"
            await self.send_message(message.sender_id, response)
            
        elif "task" in payload_lower:
            response = f"Task received! I'm a demo agent, so I'll acknowledge: '{payload}'. In production, I would execute this task."
            await self.send_message(message.sender_id, response)
            
        elif "help" in payload_lower:
            response = ("I'm a demo agent. I can respond to:\n"
                       "- Greetings (hello, hi)\n"
                       "- Status requests\n"
                       "- Task requests\n"
                       "- Help requests")
            await self.send_message(message.sender_id, response)
        else:
            response = f"Message received: '{payload}'. I'm a demo agent - type 'help' for available commands."
            await self.send_message(message.sender_id, response)
    
    async def run(self):
        """Start bidirectional streaming with authentication"""
        try:
            print(f"👂 Starting bidirectional stream for '{self.agent_id}'...")
            
            # Add token to metadata
            metadata = (('authorization', f'Bearer {self.token}'),)
            
            async for response in self.stub.StreamMessages(
                self.message_generator(),
                metadata=metadata
            ):
                # Only process messages meant for us or broadcasts
                if response.recipient_id == self.agent_id or response.recipient_id == "":
                    await self.handle_message(response)
                    
        except grpc.RpcError as e:
            print(f"❌ gRPC Error: {e}")
    
    async def close(self):
        """Close gRPC connection"""
        await self.send_queue.put(None)  # Signal generator to stop
        if self.channel:
            await self.channel.close()
            print(f"🔌 Agent '{self.agent_id}' disconnected")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python demo_agent.py <agent_id>")
        print("Example: python demo_agent.py ai-assistant-1")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    agent = DemoAgent(agent_id)
    
    try:
        await agent.connect()
        
        # Send initial greeting to announce presence (broadcast)
        await agent.send_message("", f"🤖 Agent {agent_id} is now online!", message_type=1)
        
        # Start streaming
        await agent.run()
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main())
