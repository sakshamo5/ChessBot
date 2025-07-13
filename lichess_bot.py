import requests
import json
import time
import chess
from src.ai.bot import ChessBot

class LichessBotManager:
    def __init__(self, token):
        self.token = token
        self.headers = {'Authorization': f'Bearer {token}'}
        self.base_url = 'https://lichess.org/api'
        self.seeking = False
        self.active_games = {}
        self.bot = ChessBot(depth=4)

    def upgrade_to_bot(self):
        """Upgrade account to bot account"""
        url = f"{self.base_url}/bot/account/upgrade"
        response = requests.post(url, headers=self.headers)
        return response.status_code == 200

    def get_account_info(self):
        """Get bot account information"""
        url = f"{self.base_url}/account"
        response = requests.get(url, headers=self.headers)
        return response.json() if response.status_code == 200 else None

    def get_current_rating(self, username):
        """Get current ELO ratings for all time controls"""
        url = f"{self.base_url}/user/{username}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            perfs = data.get('perfs', {})
            ratings = {}
            for time_control, perf_data in perfs.items():
                if 'rating' in perf_data:
                    ratings[time_control] = {
                        'rating': perf_data['rating'],
                        'games': perf_data.get('games', 0),
                        'rd': perf_data.get('rd', 0)
                    }
            return ratings
        return None

    def seek_game(self, time_control=10, increment=0, rated=True):
        """Seek a game automatically"""
        url = f"{self.base_url}/board/seek"
        data = {
            'time': time_control,
            'increment': increment,
            'rated': rated,
            'variant': 'standard'
        }
        response = requests.post(url, headers=self.headers, data=data)
        return response.status_code == 200

    def seek_game_flexible(self):
        """Try different time controls to find games faster"""
        time_controls = [
            (10, 0), (5, 0), (3, 0), (15, 10), (10, 5)
        ]
        
        for time_control, increment in time_controls:
            if self.seek_game(time_control, increment):
                print(f"Successfully seeking {time_control}+{increment}")
                return True
        return False

    def start_seeking_loop(self, callback_url, seek_interval=30):
        """Continuously seek games with better error handling"""
        self.seeking = True
        attempt = 0
        
        while self.seeking:
            try:
                attempt += 1
                print(f"Seeking attempt #{attempt}...")
                
                if self.seek_game_flexible():
                    print("✅ Game seek successful, waiting for opponent...")
                    time.sleep(seek_interval)
                    attempt = 0
                else:
                    print(f"❌ No games found, retrying in 10 seconds...")
                    time.sleep(10)
                    
            except Exception as e:
                print(f"Error in seeking loop: {e}")
                time.sleep(10)

    def stop_seeking(self):
        """Stop seeking games"""
        self.seeking = False

    def accept_challenge(self, challenge_id):
        """Accept a challenge"""
        url = f"{self.base_url}/challenge/{challenge_id}/accept"
        response = requests.post(url, headers=self.headers)
        return response.status_code == 200

    def make_move(self, game_id, move_uci):
        """Make a move in the game"""
        url = f"{self.base_url}/bot/game/{game_id}/move/{move_uci}"
        response = requests.post(url, headers=self.headers)
        
        if response.status_code == 200:
            print(f"✅ Move sent: {move_uci}")
            return True
        else:
            print(f"❌ Move failed: {response.status_code} - {response.text}")
            return False

    def handle_game_start(self, game_data):
        """Handle when a game starts"""
        game_id = game_data.get('game', {}).get('id')
        if not game_id:
            return
        
        print(f"🎮 Game started: {game_id}")
        
        # Stop seeking when game starts
        self.seeking = False
        
        # Initialize game state
        self.active_games[game_id] = {
            'board': chess.Board(),
            'bot_color': None
        }
        
        # Start game monitoring
        import threading
        game_thread = threading.Thread(target=self.monitor_game, args=(game_id,))
        game_thread.daemon = True
        game_thread.start()

    def handle_game_finish(self, game_data):
        """Handle when a game finishes"""
        game_id = game_data.get('game', {}).get('id')
        if game_id in self.active_games:
            del self.active_games[game_id]
        
        print(f"🏁 Game finished: {game_id}")
        
        # Resume seeking after a delay
        import threading
        def resume_seeking():
            time.sleep(5)
            if not self.active_games:  # Only resume if no active games
                callback_url = "http://localhost:5000"
                threading.Thread(target=self.start_seeking_loop, args=(callback_url,), daemon=True).start()
        
        threading.Thread(target=resume_seeking, daemon=True).start()

    def monitor_game(self, game_id):
        """Monitor game state and make moves"""
        url = f"{self.base_url}/bot/game/stream/{game_id}"
        
        try:
            with requests.get(url, headers=self.headers, stream=True) as response:
                if response.status_code != 200:
                    print(f"❌ Failed to connect to game stream: {response.status_code}")
                    return
                
                print(f"📡 Connected to game stream: {game_id}")
                
                for line in response.iter_lines():
                    if line:
                        try:
                            event = json.loads(line.decode('utf-8'))
                            self.handle_game_event(game_id, event)
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            print(f"❌ Game monitoring error: {e}")

    def handle_game_event(self, game_id, event):
        """Handle game events"""
        event_type = event.get('type')
        
        if event_type == 'gameFull':
            self.handle_game_full(game_id, event)
        elif event_type == 'gameState':
            self.handle_game_state(game_id, event)

    def handle_game_full(self, game_id, game_data):
        """Handle full game data"""
        if game_id not in self.active_games:
            return
        
        # Determine bot color
        white_player = game_data.get('white', {}).get('id', '')
        black_player = game_data.get('black', {}).get('id', '')
        
        from config import Config
        bot_username = Config.BOT_USERNAME
        
        if white_player == bot_username:
            bot_color = chess.WHITE
            print(f"🎯 Bot is WHITE vs {black_player}")
        else:
            bot_color = chess.BLACK
            print(f"🎯 Bot is BLACK vs {white_player}")
        
        # Set bot color
        self.active_games[game_id]['bot_color'] = bot_color
        self.bot.set_color(bot_color)
        
        # Process initial moves
        moves = game_data.get('state', {}).get('moves', '')
        self.process_moves(game_id, moves)
        
        # Make move if it's bot's turn
        self.check_and_make_move(game_id)

    def handle_game_state(self, game_id, game_state):
        """Handle game state updates"""
        if game_id not in self.active_games:
            return
        
        moves = game_state.get('moves', '')
        self.process_moves(game_id, moves)
        
        # Check if game is still active
        status = game_state.get('status', 'started')
        if status == 'started':
            self.check_and_make_move(game_id)

    def process_moves(self, game_id, moves_string):
        """Process moves string and update board"""
        if game_id not in self.active_games:
            return
        
        # Reset board and replay all moves
        board = chess.Board()
        
        if moves_string:
            moves = moves_string.split()
            for move_uci in moves:
                try:
                    move = chess.Move.from_uci(move_uci)
                    if move in board.legal_moves:
                        board.push(move)
                except:
                    print(f"❌ Invalid move: {move_uci}")
        
        self.active_games[game_id]['board'] = board

    def check_and_make_move(self, game_id):
        """Check if it's bot's turn and make a move"""
        if game_id not in self.active_games:
            return
        
        game_state = self.active_games[game_id]
        board = game_state['board']
        bot_color = game_state['bot_color']
        
        # Check if it's bot's turn and game is not over
        if board.turn == bot_color and not board.is_game_over():
            print(f"🎯 Bot's turn! Current position: {board.fen()}")
            
            # Get best move from bot
            best_move = self.bot.choose_move(board)
            
            if best_move:
                move_uci = best_move.uci()
                print(f"🤖 Bot choosing move: {move_uci}")
                
                # Make move locally first
                board.push(best_move)
                
                # Send move to Lichess
                self.make_move(game_id, move_uci)
            else:
                print("❌ No valid move found!")

    def stream_events(self, callback_url):
        """Stream events from Lichess"""
        url = f"{self.base_url}/stream/event"
        print(f"📡 Connecting to: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, stream=True)
            print(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Error response: {response.text}")
                return
            
            print("✅ Successfully connected to event stream...")
            
            for line in response.iter_lines():
                if line:
                    try:
                        event = json.loads(line.decode('utf-8'))
                        self.handle_event(event, callback_url)
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            print(f"❌ Stream error: {e}")

    def handle_event(self, event, callback_url):
        """Handle incoming events"""
        event_type = event.get('type')
        
        if event_type == 'challenge':
            challenge_id = event.get('challenge', {}).get('id')
            if challenge_id:
                print(f"🎯 Accepting challenge: {challenge_id}")
                self.accept_challenge(challenge_id)
                
        elif event_type == 'gameStart':
            self.handle_game_start(event)
            
        elif event_type == 'gameFinish':
            self.handle_game_finish(event)
