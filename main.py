from flask import Flask, request, jsonify
import chess
from src.ai.bot import ChessBot
from lichess_bot import LichessBotManager
from config import Config

app = Flask(__name__)

# Global variables
bot_token = None
bot_manager = None
current_ratings = {}

def update_ratings():
    """Update and display current ratings"""
    global current_ratings, bot_manager
    if bot_manager:
        new_ratings = bot_manager.get_current_rating(Config.BOT_USERNAME)
        if new_ratings:
            print("\n" + "="*50)
            print("CURRENT ELO RATINGS:")
            print("="*50)
            for time_control, rating_data in new_ratings.items():
                old_rating = current_ratings.get(time_control, {}).get('rating', 0)
                new_rating = rating_data['rating']
                games = rating_data['games']
                change = new_rating - old_rating if old_rating > 0 else 0
                change_str = f"(+{change})" if change > 0 else f"({change})" if change < 0 else ""
                print(f"{time_control.upper()}: {new_rating} {change_str} | Games: {games}")
            current_ratings = new_ratings
            print("="*50 + "\n")

@app.route('/status', methods=['GET'])
def get_status():
    """Get bot status"""
    return jsonify({
        "status": "online",
        "active_games": len(bot_manager.active_games) if bot_manager else 0,
        "ratings": current_ratings
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
