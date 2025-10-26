


import asyncio

import logging

from flyo.agent import FlyoAgent

from flyo.planner import OllamaPlanner


# Setup logging

logging.basicConfig(

    level=logging.INFO,

    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

)


logger = logging.getLogger(__name__)



def progress_callback(message: str) -> None:

    """Callback for progress updates"""

    print(f"📍 {message}")



def approval_callback(action_plan: list) -> bool:

    """Callback for plan approval"""

    print("\n" + "="*70)

    print("📋 ACTION PLAN APPROVAL REQUIRED")

    print("="*70)

   

    for i, action in enumerate(action_plan, 1):

        action_type = action.get('action', 'unknown')

        print(f"{i}. {action_type}")

       

        # Show details for risky actions

        if action_type in ["auto_login", "proceed_to_checkout", "submit_form"]:

            print(f"   ⚠️  High-risk action: {action}")

   

    print("="*70)

    response = input("\nApprove this plan? (yes/no): ").strip().lower()

   

    return response in ['yes', 'y']



async def example_search():

    """Example: Simple web search"""

    print("\n🔍 Example 1: Web Search")

    print("="*70)

   

    # Initialize planner and agent

    planner = OllamaPlanner(

        base_url="http://localhost:11434",

        model="qwen2.5-coder:7b"

    )

   

    agent = FlyoAgent(

        planner=planner,

        require_approval=False,  # No approval needed for search

        headless=False,  # Show browser for debugging

        timeout=30000

    )

   

    agent.set_log_callback(progress_callback)

   

    # Execute search task

    result = await agent.execute(

        "Search for the top 5 Python web frameworks"

    )

   

    print("\n📊 RESULT:")

    print(f"Status: {result['status']}")

    print(f"Steps executed: {result['steps_executed']}")

    print(f"Time: {result['elapsed_time']}")

    print(f"Cache hits: {result.get('cache_stats', {}).get('total_hits', 0)}")



async def example_shopping():

    """Example: E-commerce shopping with error recovery"""

    print("\n🛒 Example 2: Shopping with Auto-recovery")

    print("="*70)

   

    planner = OllamaPlanner(

        base_url="http://localhost:11434",

        model="qwen2.5-coder:7b"

    )

   

    agent = FlyoAgent(

        planner=planner,

        require_approval=True,  # Require approval for checkout

        headless=False,

        timeout=30000

    )

   

    agent.set_log_callback(progress_callback)

    agent.set_approval_callback(approval_callback)

   

    # Optional: Save credentials for auto-login

    # await agent.save_credentials("amazon.in", "your_email@example.com", "your_password")

   

    # Execute shopping task

    result = await agent.execute(

        "Find cheapest wireless mouse and add it to cart to buy on amazon"

    )

   

    print("\n📊 RESULT:")

    print(f"Status: {result['status']}")

    print(f"Steps executed: {result['steps_executed']}")

    print(f"Success rate: {result['success_rate']}")

    print(f"Self-heal attempts: {result['self_heal_attempts']}")

    print(f"Time: {result['elapsed_time']}")

   

    if result['error']:

        print(f"❌ Error: {result['error']}")



async def example_with_error_simulation():

    """Example: Demonstrate error recovery"""

    print("\n🔄 Example 3: Error Recovery Demonstration")

    print("="*70)

   

    planner = OllamaPlanner(

        base_url="http://localhost:11434",

        model="qwen2.5-coder:7b"

    )

   

    agent = FlyoAgent(

        planner=planner,

        require_approval=False,

        headless=False,

        timeout=30000

    )

   

   

    agent.set_log_callback(progress_callback)

    agent.set_approval_callback(approval_callback)

    # --- START OF ADDITION ---

    # 1. Save credentials for the domain (assuming domain is pesuacademy.com)

    print("💾 Saving credentials for pesuacademy...")

    # NOTE: Replace 'your_pesu_username' and 'your_pesu_password' with actual values

    await agent.save_credentials(

        domain="pesuacademy.com",  # Use the correct domain

        username="PES2UG23CS906",

        password="MyPass@PES"

    )

    print("✓ Credentials saved.")

    # --- END OF ADDITION ---


    # This task will now attempt to use the saved credentials for auto_login

    result = await agent.execute(

        "login to pesuacademy"

    )

   

    print("\n📊 RESULT:")

    print(f"Status: {result['status']}")

   

    if result['status'] == 'success':

        print("✅ Task completed successfully!")

        print(f"   - Steps: {result['steps_executed']}/{result['steps_planned']}")

        print(f"   - Recovery attempts: {result['self_heal_attempts']}")

        print(f"   - Time: {result['elapsed_time']}")

    else:

        print("❌ Task failed after recovery attempts")

        print(f"   - Error: {result['error']}")


async def example_credential_management():

    """Example: Save and use credentials"""

    print("\n🔐 Example 4: Credential Management")

    print("="*70)

   

    planner = OllamaPlanner(

        base_url="http://localhost:11434",

        model="qwen2.5-coder:7b"

    )

   

    agent = FlyoAgent(

        planner=planner,

        require_approval=True,

        headless=False,

        timeout=30000

    )

   

    # Save credentials (run this once)

    print("💾 Saving credentials...")

    await agent.save_credentials(

        domain="amazon.in",

        username="your_email@example.com",

        password="your_password"

    )

    print("✓ Credentials saved to credentials.json")

   

    # Now the agent can auto-login for amazon.in

    # The LLM will generate auto_login actions when it detects login pages



async def example_ui_inspection():

    """Example: Inspect current UI for debugging"""

    print("\n🔍 Example 5: UI Inspection")

    print("="*70)

   

    planner = OllamaPlanner(

        base_url="http://localhost:11434",

        model="qwen2.5-coder:7b"

    )

   

    agent = FlyoAgent(

        planner=planner,

        require_approval=False,

        headless=False,

        timeout=30000

    )

   

    # Start browser and navigate

    await agent.executor.start()

    await agent.executor.execute_action({

        "action": "navigate",

        "url": "https://example.com"

    })

   

    # Get UI context

    ui_context = await agent.get_current_ui()

   

    print("\n📄 CURRENT UI CONTEXT:")

    print(ui_context[:500])

    print("\n...")

   

    # Get full context with selectors

    full_context = await agent.executor.get_page_context()

    print("\n🎯 DISCOVERED SELECTORS:")

    print(f"Inputs: {full_context.get('selectors', {}).get('inputs', [])[:5]}")

    print(f"Buttons: {full_context.get('selectors', {}).get('buttons', [])[:5]}")

   

    await agent.executor.stop()



async def main():

    """Run examples"""

    print("""

╔══════════════════════════════════════════════════════════════════════╗

║                     FLYO ADAPTIVE AGENT EXAMPLES                     ║

║                                                                      ║

║  Features:                                                           ║

║  • Real-time UI analysis for dynamic websites                       ║

║  • Adaptive error recovery with fresh UI re-fetching                ║

║  • Smart UI caching with validation                                 ║

║  • Credential management for auto-login                             ║

║  • LLM-driven Playwright script generation                          ║

╚══════════════════════════════════════════════════════════════════════╝

    """)

   

    # Choose which example to run

    print("\nAvailable examples:")

    print("1. Web Search (simple)")

    print("2. E-commerce Shopping (with approval)")

    print("3. Error Recovery Demo")

    print("4. Credential Management")

    print("5. UI Inspection")

    print("6. Run all examples")

   

    choice = input("\nSelect example (1-6): ").strip()

   

    try:

        if choice == "1":

            await example_search()

        elif choice == "2":

            await example_shopping()

        elif choice == "3":

            await example_with_error_simulation()

        elif choice == "4":

            await example_credential_management()

        elif choice == "5":

            await example_ui_inspection()

        elif choice == "6":

            await example_search()

            await example_with_error_simulation()

            await example_shopping()

        else:

            print("Invalid choice")

            return

       

        print("\n✅ Example completed!")

       

    except KeyboardInterrupt:

        print("\n\n⚠️  Interrupted by user")

    except Exception as e:

        print(f"\n❌ Error: {e}")

        logger.exception("Example failed")



if __name__ == "__main__":

    # Run examples

    asyncio.run(main())


