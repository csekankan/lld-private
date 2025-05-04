
# Snake and Ladder Game - Python Version
# Core components: Board, Cell, Dice, Jump, Player, Game
# Patterns: Game Loop, Composition, Randomized Setup

import random
from collections import deque


class Jump:
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end


class Cell:
    def __init__(self):
        self.jump: Jump | None = None


class Dice:
    def __init__(self, dice_count=1):
        self.dice_count = dice_count
        self.min = 1
        self.max = 6

    def roll_dice(self) -> int:
        return sum(random.randint(self.min, self.max) for _ in range(self.dice_count))


class Player:
    def __init__(self, id: str, current_position: int = 0):
        self.id = id
        self.current_position = current_position


class Board:
    def __init__(self, size: int, num_snakes: int, num_ladders: int):
        self.size = size
        self.cells = [[Cell() for _ in range(size)] for _ in range(size)]
        self.add_jumps(num_snakes, num_ladders)

    def get_cell(self, position: int) -> Cell:
        row = position // self.size
        col = position % self.size
        return self.cells[row][col]

    def add_jumps(self, num_snakes: int, num_ladders: int):
        total_cells = self.size * self.size

        while num_snakes > 0:
            start = random.randint(1, total_cells - 1)
            end = random.randint(1, total_cells - 1)
            if end >= start:
                continue  # snake must go downward
            self.get_cell(start).jump = Jump(start, end)
            num_snakes -= 1

        while num_ladders > 0:
            start = random.randint(1, total_cells - 1)
            end = random.randint(1, total_cells - 1)
            if start >= end:
                continue  # ladder must go upward
            self.get_cell(start).jump = Jump(start, end)
            num_ladders -= 1


class Game:
    def __init__(self):
        self.board = Board(10, 5, 4)
        self.dice = Dice(1)
        self.players = deque([Player("p1"), Player("p2")])
        self.winner: Player | None = None

    def start(self):
        while not self.winner:
            player = self.players.popleft()
            print(f"Player turn: {player.id}, current position: {player.current_position}")

            roll = self.dice.roll_dice()
            new_position = player.current_position + roll

            if new_position >= self.board.size * self.board.size:
                self.winner = player
                break

            cell = self.board.get_cell(new_position)
            if cell.jump and cell.jump.start == new_position:
                jump_type = "ladder" if cell.jump.end > cell.jump.start else "snake"
                print(f"Hit a {jump_type}! Jumping from {cell.jump.start} to {cell.jump.end}")
                new_position = cell.jump.end

            player.current_position = new_position
            print(f"{player.id} moved to {new_position}")

            self.players.append(player)

        print(f"WINNER IS: {self.winner.id}")


if __name__ == '__main__':
    Game().start()
