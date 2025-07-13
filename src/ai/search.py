import chess
from .evaluation import evaluate_position

def minimax_search(board, depth, alpha, beta, maximizing_player):
    """
    Minimax with alpha-beta pruning for efficient search
    maximizing_player: True if current player should maximize, False if minimize
    """
    if depth == 0 or board.is_game_over():
        return evaluate_position(board), None
    
    best_move = None
    
    if maximizing_player:
        max_eval = float('-inf')
        for move in order_moves(board):
            board.push(move)
            eval_score, _ = minimax_search(board, depth - 1, alpha, beta, False)
            board.pop()
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Alpha-beta cutoff
        
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in order_moves(board):
            board.push(move)
            eval_score, _ = minimax_search(board, depth - 1, alpha, beta, True)
            board.pop()
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha-beta cutoff
        
        return min_eval, best_move

def order_moves(board):
    """Order moves for better alpha-beta pruning efficiency"""
    moves = list(board.legal_moves)
    
    # Separate move types for better ordering
    captures = []
    checks = []
    other_moves = []
    
    for move in moves:
        if board.is_capture(move):
            captures.append(move)
        elif board.gives_check(move):
            checks.append(move)
        else:
            other_moves.append(move)
    
    # Return in order: captures first, then checks, then other moves
    return captures + checks + other_moves
