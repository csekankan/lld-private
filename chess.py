# chess_design.py
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List
import random

# ========================
# ENUMS AND INTERFACES
# ========================

class Status(Enum):
    ACTIVE = 1
    WHITE_WIN = 2
    BLACK_WIN = 3
    STALEMATE = 4

class GameEventListener(ABC):
    @abstractmethod
    def on_move_made(self, move): pass

    @abstractmethod
    def on_game_state_changed(self, state): pass

class PlayerStrategy(ABC):
    @abstractmethod
    def determine_move(self, board, is_white): pass

class MovementStrategy(ABC):
    @abstractmethod
    def can_move(self, board, start_cell, end_cell): pass

# ========================
# BASIC PIECE + STRATEGY
# ========================

class Piece:
    def __init__(self, is_white: bool, strategy: MovementStrategy):
        self.is_white = is_white
        self.killed = False
        self.strategy = strategy

    def can_move(self, board, start, end):
        return self.strategy.can_move(board, start, end)

    def set_killed(self):
        self.killed = True

class KingMovement(MovementStrategy):
    def can_move(self, board, start, end):
        return abs(start.row - end.row) <= 1 and abs(start.col - end.col) <= 1

class QueenMovement(MovementStrategy):
    def can_move(self, board, start, end):
        return (start.row == end.row or start.col == end.col or
                abs(start.row - end.row) == abs(start.col - end.col))

class BishopMovement(MovementStrategy):
    def can_move(self, board, start, end):
        return abs(start.row - end.row) == abs(start.col - end.col)

# ========================
# PIECE FACTORY
# ========================

class PieceFactory:
    @staticmethod
    def create_piece(name: str, is_white: bool):
        strategies = {
            "king": KingMovement(),
            "queen": QueenMovement(),
            "bishop": BishopMovement(),
        }
        return Piece(is_white, strategies[name])

# ========================
# CELL AND BOARD
# ========================

class Cell:
    def __init__(self, row: int, col: int, piece: Optional[Piece] = None):
        self.row = row
        self.col = col
        self.piece = piece

class Board:
    _instance = None

    def __init__(self, size=8):
        self.size = size
        self.grid = [[Cell(r, c) for c in range(size)] for r in range(size)]
        self.initialize()

    @classmethod
    def get_instance(cls, size=8):
        if cls._instance is None:
            cls._instance = Board(size)
        return cls._instance

    def initialize(self):
        self.grid[0][4].piece = PieceFactory.create_piece("king", True)
        self.grid[7][4].piece = PieceFactory.create_piece("king", False)

    def get_cell(self, row, col):
        return self.grid[row][col] if 0 <= row < self.size and 0 <= col < self.size else None

# ========================
# MOVE & OBSERVER
# ========================

class Move:
    def __init__(self, start: Cell, end: Cell):
        self.start = start
        self.end = end

    def is_valid(self):
        return self.start.piece and (not self.end.piece or self.start.piece.is_white != self.end.piece.is_white)

class ConsoleGameEventListener(GameEventListener):
    def on_move_made(self, move):
        print(f"Move: ({move.start.row},{move.start.col}) -> ({move.end.row},{move.end.col})")

    def on_game_state_changed(self, state):
        print(f"Game state changed: {state.name}")

# ========================
# PLAYER AND STRATEGY
# ========================

class HumanStrategy(PlayerStrategy):
    def determine_move(self, board, is_white):
        # For demo, randomly select a move
        for row in board.grid:
            for cell in row:
                if cell.piece and cell.piece.is_white == is_white:
                    for dr in range(-1, 2):
                        for dc in range(-1, 2):
                            end = board.get_cell(cell.row + dr, cell.col + dc)
                            if end and (not end.piece or end.piece.is_white != is_white):
                                return Move(cell, end)
        return None

class Player:
    def __init__(self, name: str, is_white: bool, strategy: PlayerStrategy):
        self.name = name
        self.is_white = is_white
        self.strategy = strategy

    def make_move(self, board):
        return self.strategy.determine_move(board, self.is_white)

# ========================
# GAME CLASS
# ========================

class Game:
    def __init__(self, p1: Player, p2: Player):
        self.board = Board.get_instance()
        self.player1 = p1
        self.player2 = p2
        self.status = Status.ACTIVE
        self.listener: Optional[GameEventListener] = None
        self.white_turn = True

    def set_observer(self, listener: GameEventListener):
        self.listener = listener

    def start(self):
        while self.status == Status.ACTIVE:
            current_player = self.player1 if self.white_turn else self.player2
            move = current_player.make_move(self.board)
            if move and move.is_valid():
                self.make_move(move)
            else:
                self.status = Status.STALEMATE
                self.notify_game_state_changed()

    def make_move(self, move: Move):
        dest_piece = move.end.piece
        if isinstance(dest_piece, Piece) and isinstance(dest_piece.strategy, KingMovement):
            self.status = Status.WHITE_WIN if self.white_turn else Status.BLACK_WIN
            self.notify_game_state_changed()
        move.end.piece = move.start.piece
        move.start.piece = None
        self.white_turn = not self.white_turn
        self.notify_move_made(move)

    def notify_move_made(self, move):
        if self.listener:
            self.listener.on_move_made(move)

    def notify_game_state_changed(self):
        if self.listener:
            self.listener.on_game_state_changed(self.status)

# ========================
# MAIN FUNCTION
# ========================

if __name__ == "__main__":
    p1 = Player("Alice", True, HumanStrategy())
    p2 = Player("Bob", False, HumanStrategy())
    game = Game(p1, p2)
    game.set_observer(ConsoleGameEventListener())
    game.start()
