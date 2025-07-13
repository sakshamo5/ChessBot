import tkinter as tk
from tkinter import messagebox, filedialog
import chess
import chess.pgn
import os
import sys
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from src.ai.bot import ChessBot

class ChessGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chess Bot")
        self.root.geometry("700x650")  # Slightly wider for save/load buttons
        self.captured_white = []
        self.captured_black = []
        self.board = chess.Board()
        self.bot = ChessBot()
        self.human_color = chess.WHITE
        self.selected_square = None
        self.legal_move_squares = []
        self.flipped = False
        
        # Track full game history and current position for navigation
        self.full_game_moves = []
        self.current_position = 0
        
        self.light_color = "#F0D9B5"
        self.dark_color = "#B58863"
        self.highlight_color = "#FFFF00"
        self.legal_move_color = "#90EE90"
        
        self.create_widgets()
        self.update_board_display()
    
    def show_legal_moves(self, square):
        """Highlight legal moves for selected piece"""
        self.legal_move_squares = []
        piece = self.board.piece_at(square)
        if piece and piece.color == self.human_color:
            for move in self.board.legal_moves:
                if move.from_square == square:
                    self.legal_move_squares.append(move.to_square)
    
    def update_move_history(self):
        """Update move history with clickable entries"""
        self.history_listbox.delete(0, tk.END)
        
        temp_board = chess.Board()
        move_number = 1
        
        for i, move in enumerate(self.full_game_moves):
            move_text = temp_board.san(move)
            
            if i % 2 == 0:
                entry = f"{move_number}. {move_text}"
                self.history_listbox.insert(tk.END, entry)
                move_number += 1
            else:
                current_entry = self.history_listbox.get(tk.END)
                updated_entry = f"{current_entry} {move_text}"
                self.history_listbox.delete(tk.END)
                self.history_listbox.insert(tk.END, updated_entry)
            
            temp_board.push(move)
        
        if self.history_listbox.size() > 0:
            self.history_listbox.see(tk.END)

    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - chess board
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT)
        self.board_frame = tk.Frame(left_frame)
        self.board_frame.pack(pady=10)
        self.squares = {}
        
        # Right side - move history and controls
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(20, 0))
        
        tk.Label(right_frame, text="Move History", font=("Arial", 12, "bold")).pack()
        
        # Navigation controls
        nav_frame = tk.Frame(right_frame)
        nav_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(nav_frame, text="◀◀ Start", command=self.jump_to_start, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="◀ Back", command=self.step_back, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="Forward ▶", command=self.step_forward, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="End ▶▶", command=self.jump_to_end, width=8).pack(side=tk.LEFT, padx=2)
        
        # Move history listbox
        history_frame = tk.Frame(right_frame)
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        self.history_listbox = tk.Listbox(history_frame, width=25, height=12, font=("Arial", 10), selectmode=tk.SINGLE)
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(history_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.history_listbox.yview)
        self.history_listbox.bind('<Double-Button-1>', self.on_move_click)
        
        # Save/Load buttons
        file_frame = tk.Frame(right_frame)
        file_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(file_frame, text="Save Game", command=self.save_game, width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="Load Game", command=self.load_game, width=12).pack(side=tk.LEFT, padx=2)
        
        # Captured pieces
        captured_frame = tk.Frame(right_frame)
        captured_frame.pack(fill=tk.X, pady=(20, 0))
        tk.Label(captured_frame, text="Captured Pieces", font=('Arial', 12, 'bold')).pack()
        
        self.white_captured_label = tk.Label(captured_frame, text="Black captured: ", font=("Arial", 10), justify=tk.LEFT, wraplength=180)
        self.white_captured_label.pack(anchor=tk.W, pady=(5, 0))
        
        self.black_captured_label = tk.Label(captured_frame, text="White captured: ", font=("Arial", 10), justify=tk.LEFT, wraplength=180)
        self.black_captured_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Evaluation
        eval_frame = tk.Frame(right_frame)
        eval_frame.pack(fill=tk.X, pady=(20, 0))
        tk.Label(eval_frame, text="Position Evaluation", font=("Arial", 12, "bold")).pack()
        self.eval_label = tk.Label(eval_frame, text="Evaluation: 0.00", font=("Arial", 11), fg="blue")
        self.eval_label.pack(pady=(5, 0))
        
        self.create_board()
        
        # Status label
        self.status_label = tk.Label(left_frame, text="White to move", font=("Arial", 14))
        self.status_label.pack(pady=10)
        
        # Control buttons
        button_frame = tk.Frame(left_frame)
        button_frame.pack()
        
        tk.Button(button_frame, text="New Game", command=self.new_game).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Choose Color", command=self.choose_color).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Undo Move", command=self.undo_move).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Flip Board", command=self.flip_board).pack(side=tk.LEFT, padx=5)

    def create_board(self):
        """Create or recreate the chess board with proper orientation"""
        for widget in self.board_frame.winfo_children():
            widget.destroy()
        
        self.squares = {}
        board_container = tk.Frame(self.board_frame)
        board_container.pack()
        
        if self.flipped:
            files = "hgfedcba"
            ranks = range(1, 9)
        else:
            files = "abcdefgh"
            ranks = range(8, 0, -1)
        
        # Top file labels
        top_frame = tk.Frame(board_container)
        top_frame.pack()
        tk.Label(top_frame, text="  ", width=2).pack(side=tk.LEFT)
        for file_letter in files:
            tk.Label(top_frame, text=file_letter, width=7, font=('Arial', 10)).pack(side=tk.LEFT)
        
        # Create the 8x8 board
        for i, rank in enumerate(ranks):
            row_frame = tk.Frame(board_container)
            row_frame.pack()
            
            tk.Label(row_frame, text=str(rank), width=2, font=('Arial', 10)).pack(side=tk.LEFT)
            
            for j, file_letter in enumerate(files):
                square_name = f"{file_letter}{rank}"
                
                file_idx = ord(file_letter) - ord('a')
                rank_idx = rank - 1
                if (file_idx + rank_idx) % 2 == 1:
                    bg_color = self.light_color
                else:
                    bg_color = self.dark_color
                
                button = tk.Button(
                    row_frame,
                    width=4,
                    height=2,
                    bg=bg_color,
                    font=('Arial', 18),
                    command=lambda sq=square_name: self.on_square_click(sq)
                )
                button.pack(side=tk.LEFT)
                self.squares[square_name] = button
        
        # Bottom file labels
        bottom_frame = tk.Frame(board_container)
        bottom_frame.pack()
        tk.Label(bottom_frame, text=" ", width=2).pack(side=tk.LEFT)
        for file_letter in files:
            tk.Label(bottom_frame, text=file_letter, width=7, font=("Arial", 10)).pack(side=tk.LEFT)

    def flip_board(self):
        """Flip the board orientation"""
        self.flipped = not self.flipped
        self.create_board()
        self.update_board_display()

    def track_capture(self, move):
        captured_piece = self.board.piece_at(move.to_square)
        if captured_piece:
            if captured_piece.color == chess.WHITE:
                self.captured_white.append(captured_piece)
            else:
                self.captured_black.append(captured_piece)
    
    def update_evaluation_display(self):
        """Update the position evaluation display"""
        eval_score = self.bot.get_evaluation(self.board)
        eval_text = f"Evaluation: {eval_score/100:+.2f}"
        if eval_score > 50:
            color = "green" 
        elif eval_score < -50:
            color = "red"   
        else:
            color = "blue"
        self.eval_label.config(text=eval_text, fg=color)
        
    def update_captured_display(self):
        white_symbols = [self.get_piece_symbol(piece) for piece in self.captured_white]
        black_symbols = [self.get_piece_symbol(piece) for piece in self.captured_black]
        
        self.white_captured_label.config(text=f"Black captured: {''.join(white_symbols)}")
        self.black_captured_label.config(text=f"White captured: {''.join(black_symbols)}")
    
    def get_piece_symbol(self, piece):
        """Convert chess piece to Unicode symbol"""
        piece_symbols = {
            chess.PAWN: {"white": "♙", "black": "♟"},
            chess.ROOK: {"white": "♖", "black": "♜"},
            chess.KNIGHT: {"white": "♘", "black": "♞"},
            chess.BISHOP: {"white": "♗", "black": "♝"},
            chess.QUEEN: {"white": "♕", "black": "♛"},
            chess.KING: {"white": "♔", "black": "♚"}
        }
        if piece is None:
            return ""
        color = "white" if piece.color == chess.WHITE else "black"
        return piece_symbols[piece.piece_type][color]
    
    def update_board_display(self):
        """Update the visual board with current position"""
        for square_name, button in self.squares.items():
            square = chess.parse_square(square_name)
            piece = self.board.piece_at(square)
            
            button.config(text=self.get_piece_symbol(piece))
            
            file_idx = ord(square_name[0]) - ord('a')
            rank_idx = int(square_name[1]) - 1
            if (file_idx + rank_idx) % 2 == 1:
                bg_color = self.light_color
            else:
                bg_color = self.dark_color
            
            if square in self.legal_move_squares:
                bg_color = self.legal_move_color
            
            if square == self.selected_square:
                bg_color = self.highlight_color
            
            button.config(bg=bg_color)
        
        if self.current_position < len(self.full_game_moves):
            self.status_label.config(text=f"Viewing move {self.current_position} of {len(self.full_game_moves)}")
        else:
            if self.board.turn == chess.WHITE:
                turn_text = "White to move"
            else:
                turn_text = "Black to move"
            
            if self.board.is_check():
                turn_text += " (CHECK!)"
            
            self.status_label.config(text=turn_text)
        
        self.update_move_history()
        self.update_evaluation_display()
    
    def on_square_click(self, square_name):
        """Handle square clicks for move input"""
        if self.current_position < len(self.full_game_moves):
            return
            
        square = chess.parse_square(square_name)
        
        if self.board.turn != self.human_color:
            return
        
        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.human_color:
                self.selected_square = square
                self.show_legal_moves(square)
                self.update_board_display()
        else:
            self.legal_move_squares = []
            try:
                move = chess.Move(self.selected_square, square)
                
                if (self.board.piece_at(self.selected_square).piece_type == chess.PAWN and
                    chess.square_rank(square) in [0, 7]):
                    move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)
                
                if move in self.board.legal_moves:
                    self.track_capture(move)
                    self.board.push(move)
                    self.full_game_moves.append(move)
                    self.current_position = len(self.full_game_moves)
                    self.selected_square = None
                    self.update_board_display()
                    self.update_captured_display()
                    
                    if self.board.is_game_over():
                        self.handle_game_over()
                    else:
                        self.root.after(500, self.make_bot_move)
                else:
                    self.selected_square = None
                    self.update_board_display()
            except:
                self.selected_square = None
                self.update_board_display()
    
    def make_bot_move(self):
        """Make the bot's move"""
        if not self.board.is_game_over() and self.board.turn != self.human_color:
            self.status_label.config(text="Bot is thinking...")
            self.root.update()
            
            bot_move = self.bot.choose_move(self.board)
            self.track_capture(bot_move)
            self.board.push(bot_move)
            self.full_game_moves.append(bot_move)
            self.current_position = len(self.full_game_moves)
            self.update_board_display()
            self.update_captured_display()
            
            if self.board.is_game_over():
                self.handle_game_over()
    
    def save_game(self):
        """Save current game to PGN file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pgn",
            filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")]
        )
        if filename:
            game = chess.pgn.Game()
            game.headers["Event"] = "Chess Bot Game"
            game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
            game.headers["White"] = "Human" if self.human_color == chess.WHITE else "Bot"
            game.headers["Black"] = "Bot" if self.human_color == chess.WHITE else "Human"
            game.headers["Result"] = self.board.result()
            
            node = game
            temp_board = chess.Board()
            for move in self.full_game_moves:
                node = node.add_variation(move)
                temp_board.push(move)
            
            with open(filename, 'w') as f:
                print(game, file=f)
            
            messagebox.showinfo("Save Game", f"Game saved to {filename}")
    
    def load_game(self):
        """Load game from PGN file"""
        filename = filedialog.askopenfilename(
            filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    game = chess.pgn.read_game(f)
                
                if game:
                    self.board = chess.Board()
                    self.full_game_moves = []
                    self.current_position = 0
                    self.captured_white = []
                    self.captured_black = []
                    
                    for move in game.mainline_moves():
                        self.track_capture(move)
                        self.board.push(move)
                        self.full_game_moves.append(move)
                    
                    self.current_position = len(self.full_game_moves)
                    self.update_board_display()
                    self.update_captured_display()
                    
                    messagebox.showinfo("Load Game", f"Game loaded from {filename}")
                else:
                    messagebox.showerror("Load Game", "Invalid PGN file")
            except Exception as e:
                messagebox.showerror("Load Game", f"Error loading game: {str(e)}")
    
    def jump_to_start(self):
        self.current_position = 0
        self.jump_to_position([])

    def jump_to_end(self):
        self.current_position = len(self.full_game_moves)
        self.jump_to_position(self.full_game_moves)

    def step_back(self):
        if self.current_position > 0:
            self.current_position -= 1
            target_moves = self.full_game_moves[:self.current_position]
            self.jump_to_position(target_moves)

    def step_forward(self):
        if self.current_position < len(self.full_game_moves):
            self.current_position += 1
            target_moves = self.full_game_moves[:self.current_position]
            self.jump_to_position(target_moves)

    def on_move_click(self, event):
        selection = self.history_listbox.curselection()
        if selection:
            line_index = selection[0]
            self.jump_to_move_line(line_index)

    def jump_to_move_line(self, line_index):
        target_moves = []
        for i, move in enumerate(self.full_game_moves):
            current_line = i // 2
            if current_line <= line_index:
                target_moves.append(move)
            else:
                break
        
        self.current_position = len(target_moves)
        self.jump_to_position(target_moves)

    def jump_to_position(self, moves_to_play):
        self.board = chess.Board()
        self.captured_white = []
        self.captured_black = []
        
        for move in moves_to_play:
            self.track_capture(move)
            self.board.push(move)
        
        self.selected_square = None
        self.legal_move_squares = []
        self.update_board_display()
        self.update_captured_display()
    
    def handle_game_over(self):
        result = self.board.result()
        if result == "1-0":
            message = "White Wins!"
        elif result == "0-1":
            message = "Black Wins!"
        else:
            message = "It's a draw!"
        messagebox.showinfo("Game Over", message)
    
    def new_game(self):
        self.board = chess.Board()
        self.full_game_moves = []
        self.current_position = 0
        self.selected_square = None
        self.legal_move_squares = []
        self.captured_white = []  
        self.captured_black = []
        self.update_board_display()
        self.update_captured_display()
        
        if self.human_color == chess.BLACK:
            self.root.after(500, self.make_bot_move)
    
    def choose_color(self):
        choice = messagebox.askyesno("Choose Color", "Play as White? (No = Black)")
        self.human_color = chess.WHITE if choice else chess.BLACK
        
        # Set bot's color (opposite of human)
        bot_color = chess.BLACK if self.human_color == chess.WHITE else chess.WHITE
        self.bot.set_color(bot_color)
        
        if self.human_color == chess.BLACK and not self.flipped:
            self.flipped = True
            self.create_board()
        elif self.human_color == chess.WHITE and self.flipped:
            self.flipped = False
            self.create_board()
            
        self.new_game()

    
    def undo_move(self):
        if len(self.full_game_moves) >= 2:
            self.full_game_moves = self.full_game_moves[:-2]
            self.current_position = len(self.full_game_moves)
            self.jump_to_position(self.full_game_moves)
        elif len(self.full_game_moves) == 1:
            self.full_game_moves = []
            self.current_position = 0
            self.jump_to_position([])
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    gui = ChessGUI()
    gui.run()
