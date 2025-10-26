from flask import Flask, request, jsonify, render_template
from llm_planner import LLMPlanner
from executor import FlyoExecutor
import atexit
import webbrowser
import threading
import time
import os
from dotenv import load_dotenv

# Load environment variables from user.env file
load_dotenv('user.env')  # Specify the custom filename

app = Flask(__name__)

# Initialize components
try:
    planner = LLMPlanner()
    
    # Set headless=False to see the browser automation
    executor = FlyoExecutor(planner, headless=False)
    
    atexit.register(executor.close)

    # Check if credentials are configured
    credentials_configured = {
        "Amazon": bool(os.getenv("AMAZON_EMAIL") and os.getenv("AMAZON_PASSWORD")),
        "Flipkart": bool(os.getenv("FLIPKART_EMAIL") and os.getenv("FLIPKART_PASSWORD"))
    }
    
    print("\n" + "="*60)
    print("🔐 CREDENTIAL STATUS")
    print("="*60)
    for site, configured in credentials_configured.items():
        status = "✅ Configured" if configured else "⚠️  Not configured"
        print(f"{site}: {status}")
    print("="*60)
    
    if not any(credentials_configured.values()):
        print("\n⚠️  WARNING: No login credentials configured!")
        print("📝 To enable auto-login:")
        print("   1. Create a .env file in the project directory")
        print("   2. Add your credentials (see .env_template for format)")
        print("   3. Restart the application")
        print("="*60 + "\n")

except Exception as e:
    print(f"FATAL: Failed to initialize Flyo components: {e}")


def open_browser():
    """Opens the Flyo interface in the default browser after a short delay"""
    time.sleep(1.5)  # Wait for server to start
    webbrowser.open('http://localhost:5000')
    print("\n🌐 Opened Flyo interface in your default browser")


@app.route('/')
def home():
    """Serves the main HTML interface."""
    return render_template('index.html')


@app.route('/run', methods=['POST'])
def run():
    """Handles the user search command and returns product list."""
    data = request.get_json()
    user_command = data.get("command", "")
    if not user_command:
        return jsonify({"error": "No command provided"}), 400

    if 'executor' not in locals() and 'executor' not in globals():
        return jsonify({"error": "System is not initialized. Check server logs."}), 500

    print(f"\n{'='*60}")
    print(f"SEARCH REQUEST: {user_command}")
    print(f"{'='*60}\n")
    
    try:
        # Only search and return items, don't add to cart yet
        result = executor.search_products(user_command)
        return jsonify(result)
    except Exception as e:
        print(f"Search failed with error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/checkout', methods=['POST'])
def checkout():
    """Handles adding selected item to cart and proceeding to checkout."""
    data = request.get_json()
    selected_item = data.get("item")
    
    if not selected_item:
        return jsonify({"error": "No item provided"}), 400

    if 'executor' not in locals() and 'executor' not in globals():
        return jsonify({"error": "System is not initialized"}), 500

    print(f"\n{'='*60}")
    print(f"CHECKOUT REQUEST")
    print(f"Item: {selected_item['name']}")
    print(f"Price: ₹{selected_item['price']}")
    print(f"Website: {selected_item['website']}")
    print(f"{'='*60}\n")
    
    try:
        # Execute the full checkout automation with auto-login
        result = executor.proceed_to_checkout(selected_item)
        return jsonify(result)
    except Exception as e:
        print(f"Checkout failed with error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 FLYO E-COMMERCE ASSISTANT STARTING")
    print("="*60)
    print("⚙️  Running in NON-HEADLESS mode (you'll see the browser)")
    print("🔐 Auto-login: Enabled (if credentials configured)")
    print("🌐 Server running at: http://localhost:5000")
    print("📱 Opening interface automatically...")
    print("="*60 + "\n")
    
    # Start a thread to open the browser after server starts
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(debug=False, use_reloader=False, threaded=False)