import chess

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

def evaluate_material(board):
    white_material = 0
    black_material = 0
    
    # Count material for both sides
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            piece_value = PIECE_VALUES[piece.piece_type]
            if piece.color == chess.WHITE:
                white_material += piece_value
            else:
                black_material += piece_value
    
    return white_material - black_material

def evaluate_position(board):
    material_score = evaluate_material(board)
    
    positional_score = 0
    
    # Center control bonus
    center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
    for square in center_squares:
        piece = board.piece_at(square)
        if piece is not None:  # FIXED: Check for None first!
            if piece.color == chess.WHITE:
                positional_score += 10  # FIXED: Use += not =+
            else:
                positional_score -= 10  # FIXED: Use -= not =-
    
    # Development bonus
    development_bonus = evaluate_development(board)
    positional_score += development_bonus  # FIXED: Use += not =+
    
    return material_score + positional_score

def evaluate_development(board):
    development_score = 0
    
    # White piece development
    if board.piece_at(chess.B1) != chess.Piece(chess.KNIGHT, chess.WHITE):
        development_score += 10  # FIXED: Use += not =+
    if board.piece_at(chess.G1) != chess.Piece(chess.KNIGHT, chess.WHITE):
        development_score += 10
    if board.piece_at(chess.C1) != chess.Piece(chess.BISHOP, chess.WHITE):
        development_score += 10
    if board.piece_at(chess.F1) != chess.Piece(chess.BISHOP, chess.WHITE):
        development_score += 10
    
    # Black piece development
    if board.piece_at(chess.B8) != chess.Piece(chess.KNIGHT, chess.BLACK):
        development_score -= 10  # FIXED: Use -= not =-
    if board.piece_at(chess.G8) != chess.Piece(chess.KNIGHT, chess.BLACK):
        development_score -= 10
    if board.piece_at(chess.C8) != chess.Piece(chess.BISHOP, chess.BLACK):
        development_score -= 10
    if board.piece_at(chess.F8) != chess.Piece(chess.BISHOP, chess.BLACK):
        development_score -= 10
    
    return development_score

