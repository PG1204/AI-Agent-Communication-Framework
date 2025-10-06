import asyncio
import os
from intelligent_agent import IntelligentAgent

SYSTEM_PROMPT = """You are a Research Agent specialized in gathering and analyzing information.
Your role is to:
- Search for and synthesize information on technical topics
- Recommend best libraries, tools, and approaches
- Provide comparisons and trade-offs
- Stay up-to-date with latest technologies

Keep responses concise (2-3 paragraphs max) and actionable. Focus on practical recommendations."""

async def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Please set GROQ_API_KEY environment variable")
        print("   Get your free key at: https://console.groq.com")
        return
    
    agent = IntelligentAgent(
        agent_id="research-agent",
        system_prompt=SYSTEM_PROMPT,
        groq_api_key=api_key
    )
    
    print("🔬 Research Agent starting...")
    await agent.connect()

if __name__ == "__main__":
    asyncio.run(main())
