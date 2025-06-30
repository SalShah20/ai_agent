import logging
logging.basicConfig(level=logging.DEBUG)
from langchain_openai import ChatOpenAI
from browser_use import Agent
from dotenv import load_dotenv
load_dotenv()

import asyncio

llm = ChatOpenAI(model="gpt-3.5-turbo")

async def main():
    agent = Agent(
        task="Open google.com and search for the price comparison of iPhone 13 and Samsung Galazxy S21. Extract their information and compare the prices.",
        llm=llm,
    )
    try:
        result = await asyncio.wait_for(agent.run(), timeout=60)
        print(result)
    except asyncio.TimeoutError:
        print("⏰ Timed out while running the agent. It may be stuck.")

asyncio.run(main())