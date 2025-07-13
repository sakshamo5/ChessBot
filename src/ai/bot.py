import chess
from .evaluation import evaluate_position
from .search import minimax_search

class ChessBot:
    def __init__(self, depth=4):
        self.name = "SmartBot"
        self.search_depth = depth
        self.bot_color = None
    
    def set_color(self, color):
        """Set the bot's color (WHITE or BLACK)"""
        self.bot_color = color
    
    def choose_move(self, board):
        """Choose best move using minimax search"""
        if not board.legal_moves:
            return None
        
        # Set bot color if not already set
        if self.bot_color is None:
            self.bot_color = board.turn
        
        # Determine if bot should maximize or minimize
        bot_is_maximizing = (self.bot_color == chess.WHITE)
        
        _, best_move = minimax_search(
            board, 
            self.search_depth, 
            float('-inf'), 
            float('inf'), 
            bot_is_maximizing
        )
        
        return best_move if best_move else list(board.legal_moves)[0]
    
    def get_evaluation(self, board):
        """Get current position evaluation from bot's perspective"""
        eval_score = evaluate_position(board)
        
        # If bot is black, flip the evaluation score
        if self.bot_color == chess.BLACK:
            eval_score = -eval_score
            
        return eval_score
