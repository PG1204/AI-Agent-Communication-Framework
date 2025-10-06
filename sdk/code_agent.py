import asyncio
import os
from intelligent_agent import IntelligentAgent

SYSTEM_PROMPT = """You are a Code Agent specialized in writing, debugging, and explaining code.
Your role is to:
- Write clean, efficient, and well-documented code
- Debug code and fix errors
- Explain code line-by-line when requested
- Recommend best practices and design patterns
- Support multiple programming languages (Python, JavaScript, Java, etc.)

Keep code examples concise but complete. Include comments for clarity."""

async def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Please set GROQ_API_KEY environment variable")
        return
    
    agent = IntelligentAgent(
        agent_id="code-agent",
        system_prompt=SYSTEM_PROMPT,
        groq_api_key=api_key
    )
    
    print("💻 Code Agent starting...")
    await agent.connect()

if __name__ == "__main__":
    asyncio.run(main())
