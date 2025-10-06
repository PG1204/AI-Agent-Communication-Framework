import asyncio
import os
from intelligent_agent import IntelligentAgent
from agent_comm_pb2 import AgentMessage
import json

class SmartCoordinator(IntelligentAgent):
    def __init__(self, agent_id: str, groq_api_key: str):
        system_prompt = """You are a Smart Coordinator that orchestrates tasks between specialist agents in real-time.

Available specialists:
- research-agent: Technical research, recommendations, comparisons, best practices
- code-agent: Code writing, debugging, explanations, implementation details

When handling requests:
1. Analyze if the task requires research, coding, or both
2. For complex multi-part requests, coordinate with both agents
3. Synthesize responses from specialists into comprehensive answers
4. Always provide actionable, complete solutions

Be direct, efficient, and thorough in coordinating responses."""
        
        super().__init__(agent_id, system_prompt, groq_api_key)
        self.specialists = ["research-agent", "code-agent"]
    
    async def coordinate_request(self, user_message, sender):
        """Coordinate a complex request across multiple agents"""
        print(f"🎯 Coordinating request: {user_message}")
        
        # Determine what each agent should handle
        research_needed = any(keyword in user_message.lower() for keyword in 
                            ['choose', 'recommend', 'best', 'compare', 'stack', 'technology', 'tool', 'library'])
        
        code_needed = any(keyword in user_message.lower() for keyword in 
                         ['code', 'implement', 'write', 'example', 'starter', 'sample', 'api', 'function'])
        
        responses = {}
        
        # Send requests to appropriate agents
        if research_needed:
            research_request = f"Research request: {user_message}"
            req_id = await self.request_from_agent("research-agent", research_request)
            research_response = await self.wait_for_agent_response(req_id, timeout=15)
            if research_response:
                responses["research"] = research_response
                print("✅ Got research response")
        
        if code_needed:
            code_request = f"Code request: {user_message}"
            req_id = await self.request_from_agent("code-agent", code_request)
            code_response = await self.wait_for_agent_response(req_id, timeout=15)
            if code_response:
                responses["code"] = code_response
                print("✅ Got code response")
        
        # Synthesize the responses
        if responses:
            synthesis_prompt = f"""Synthesize these specialist responses into one comprehensive answer for: "{user_message}"

Research Response: {responses.get('research', 'N/A')}

Code Response: {responses.get('code', 'N/A')}

Provide a unified, actionable response that combines both perspectives."""
            
            final_response = await self.get_ai_response(sender, synthesis_prompt)
        else:
            # Handle directly if no specialists needed
            final_response = await self.get_ai_response(sender, user_message)
        
        return final_response
    
    async def handle_incoming(self, response_stream):
        """Enhanced message handling with coordination"""
        async for msg in response_stream:
            sender = msg.sender_id
            payload = msg.payload.decode('utf-8')
            
            # Handle agent communication first
            if sender.endswith('-agent'):
                try:
                    data = json.loads(payload)
                    if data.get("type") == "agent_request":
                        await self.handle_agent_request(sender, data)
                        continue
                    elif data.get("type") == "agent_response":
                        await self.handle_agent_response(sender, data)
                        continue
                except (json.JSONDecodeError, KeyError):
                    continue
            
            print(f"📨 Received from {sender}: {payload}")
            
            # Check if this needs coordination
            needs_coordination = any(keyword in payload.lower() for keyword in 
                                   ['build', 'create', 'develop', 'implement', 'choose and write', 'stack and code'])
            
            if needs_coordination:
                print("🎯 This requires multi-agent coordination!")
                response = await self.coordinate_request(payload, sender)
            else:
                # Handle simple requests directly
                response = await self.get_ai_response(sender, payload)
            
            # Send response back
            await self.send_message(
                message_type=AgentMessage.DIRECT,
                recipient_id=sender,
                payload=response
            )
            print(f"📤 Sent coordinated response to {sender}")

async def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Please set GROQ_API_KEY environment variable")
        return
    
    coordinator = SmartCoordinator("smart-coordinator", api_key)
    
    print("🎯 Smart Coordinator starting...")
    await coordinator.connect()

if __name__ == "__main__":
    asyncio.run(main())
