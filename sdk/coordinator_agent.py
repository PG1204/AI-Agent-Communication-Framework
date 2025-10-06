import asyncio
import os
from intelligent_agent import IntelligentAgent

SYSTEM_PROMPT = """You are a Coordinator Agent that orchestrates tasks between specialist agents.

Available specialists:
- research-agent: Technical research, tool recommendations, comparisons  
- code-agent: Writing code, debugging, code explanations

For complex tasks requiring multiple agents:
1. Analyze the request and identify what each specialist should handle
2. Send specific requests to agents using the format: "REQUEST TO [agent]: [specific task]"
3. Wait for their responses, then synthesize a comprehensive answer

For simple tasks, handle them directly or route to the appropriate single agent.

Always provide immediate, actionable responses. Be concise but thorough."""

async def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Please set GROQ_API_KEY environment variable")
        return
    
    agent = IntelligentAgent(
        agent_id="coordinator-agent",
        system_prompt=SYSTEM_PROMPT,
        groq_api_key=api_key
    )
    
    print("🎯 Coordinator Agent starting...")
    await agent.connect()

if __name__ == "__main__":
    asyncio.run(main())
