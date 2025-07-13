import threading
import time
import requests
from main import app
from lichess_bot import LichessBotManager
from config import Config
import main
from flask import Flask
import os

app = Flask(__name__)

def test_connection():
    """Test Lichess API connection"""
    headers = {'Authorization': f'Bearer {Config.LICHESS_TOKEN}'}
    try:
        response = requests.get('https://lichess.org/api/account', headers=headers)
        if response.status_code == 200:
            account_info = response.json()
            print(f"Connected as: {account_info.get('username')}")
            return True
        else:
            print(f" Connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f" Connection error: {e}")
        return False

def start_flask_app():
    """Start Flask application"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def start_bot_system():
    """Start the complete bot system"""
    bot_manager = LichessBotManager(Config.LICHESS_TOKEN)
    main.bot_manager = bot_manager
    
    print("🤖 Upgrading to bot account...")
    upgrade_result = bot_manager.upgrade_to_bot()
    if upgrade_result:
        print("Bot account upgrade successful")
    else:
        print("Bot account upgrade failed (might already be a bot)")
    
    # Get initial ratings
    main.update_ratings()
    
    callback_url = f"http://{Config.FLASK_HOST}:{Config.FLASK_PORT}"
    
    # Start seeking games in a separate thread
    print("🎯 Starting game seeking...")
    seeking_thread = threading.Thread(
        target=bot_manager.start_seeking_loop,
        args=(callback_url,),
        daemon=True
    )
    seeking_thread.start()
    
    # Start streaming events (this will block)
    print("📡 Starting event streaming...")
    bot_manager.stream_events(callback_url)

@app.route('/')
def health_check():
    return "Chess Bot is running!"

if __name__ == '__main__':
    print("Starting Chess Bot...")
    print("="*50)
    
    # Test connection first
    if not test_connection():
        print("Exiting due to connection failure")
        exit(1)
    
    # Set the bot token in main module
    main.bot_token = Config.LICHESS_TOKEN
    
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=start_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Wait a moment for Flask to start
    time.sleep(2)
    
    # Start the bot system
    start_bot_system()
