"""
Basic FLYO Example - Google Search
Run with: python examples/example_basic.py
"""

import asyncio
from flyo import FlyoAgent, OpenAIPlanner


async def main():
    """Simple Google search example"""
    
    # Initialize planner (requires OPENAI_API_KEY environment variable)
    planner = OpenAIPlanner(model="gpt-3.5-turbo")
    
    # Initialize agent
    agent = FlyoAgent(
        planner=planner,
        require_approval=False,  # Skip approval for simple search
        headless=False  # Show browser window
    )
    
    # Execute task
    print("🤖 FLYO - Automating Google search...")
    
    result = await agent.execute("Go to Google and search for 'browser automation with AI'")
    
    # Print results
    print("\n" + "="*50)
    print("EXECUTION RESULT")
    print("="*50)
    print(f"Status: {result['status']}")
    print(f"Steps executed: {result['steps_executed']}/{result['steps_planned']}")
    print(f"Time taken: {result['elapsed_time']}")
    
    if result['error']:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())
