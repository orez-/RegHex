import itertools
import os.path
import random
import string

import get_key


def get_words(size):
    with open(os.path.expanduser('~/Desktop/python_sundry/dictionary.txt')) as f:
        groups = itertools.groupby(f, lambda x: x[0].lower())
        for _ in range(3):
            letter, word_group = next(groups)
            group = sorted(
                word.strip()
                for word in random.sample(list(word_group), size * 2 - 1)
            )
            yield group


def start_of_row(y, size):
    return -min(y, 0) - size


def print_board(board, hilite):
    size = SIZE - 1
    hx, hy = hilite

    max_width = max(
        len(clue.clue) - abs(y)
        for y, clue in enumerate(board.clues[0], -size)
    )

    top = iter(board.clues[1][::-1])
    bottom = iter([''] + board.clues[2][::-1])

    # Top
    for y, word in zip(range(SIZE + 1), top):
        # 3 is the length of the space between the left words and the hex.
        print(' ' * (max_width + 3 + SIZE * 2 - y) + '/ ' * y + str(word))

    # Main hex part
    for y, word in enumerate(board.clues[0], -size):
        print('{:>{}}'.format(str(word), max_width + abs(y)), end=' ─ ')
        start = start_of_row(y, size)
        for x, letter in enumerate(word.text, start):
            if x == hx and y == hy:
                print(end='! ')
            else:
                print(letter or '.', end=' ')
        if y < 0:
            print('/', next(top, ''))
        elif y > 0:
            print('\\', next(bottom))
        else:
            print()

    for y, word in enumerate(bottom, -SIZE):
        # 3 is the length of the space between the left words and the hex.
        print(' ' * (max_width + 3 + SIZE * 2 + y) + '\\ ' * abs(y) + str(word))


def coordinate(x, y, z=None):
    coords = x, y, z
    nones = sum(c is None for c in coords)
    if nones > 1:
        raise TypeError("At least two coordinate values must be provided.")
    if nones == 1:
        final_coord = -sum(c for c in coords if c is not None)
        coords = tuple(c if c is not None else final_coord for c in coords)
    elif sum(coords):
        raise ValueError("Coordinate values must sum to 0.")
    return coords


class ClueRow:
    def __init__(self, clue, length):
        self.clue = clue
        self.text = [None] * length

    def set_char(self, pos, char):
        print(len(self.text))
        self.text[pos] = char
        # TODO: revalidation

    def __str__(self):
        return self.clue


class HexBoard:
    def __init__(self, clues, size):
        self.size = size
        self.clues = [
            [
                ClueRow(clue_row, (size - 1) * 2 - abs(i) + 1)
                for i, clue_row in enumerate(clue_side, -size + 1)
            ]
            for clue_side in clues
        ]

    def out_of_bounds(self, x, y):
        return abs(x) >= self.size or abs(y) >= self.size or abs(x + y) >= self.size

    def set_char(self, coord, char):
        coord = coordinate(*coord)
        for i in range(3):
            down = self.size + coord[i - 2] - 1
            over = coord[i] - start_of_row(coord[i - 2], self.size - 1)
            self.clues[i][down].set_char(over, char)


if __name__ == '__main__':
    SIZE = 4
    board = HexBoard(get_words(SIZE), SIZE)

    x = 0
    y = 0
    ch = None
    while ch != '\x03':
        print_board(board, (x, y))
        ch = get_key.getch()
        if ch == get_key.LEFT_ARROW:
            if not board.out_of_bounds(x - 1, y):
                x -= 1
        elif ch == get_key.RIGHT_ARROW:
            if not board.out_of_bounds(x + 1, y):
                x += 1
        elif ch == get_key.UP_ARROW:
            if y % 2 and not board.out_of_bounds(x + 1, y - 1):
                x += 1
            if not board.out_of_bounds(x, y - 1):
                y -= 1
        elif ch == get_key.DOWN_ARROW:
            if not (y % 2) and not board.out_of_bounds(x - 1, y + 1):
                x -= 1
            if not board.out_of_bounds(x, y + 1):
                y += 1
        elif ch in string.ascii_letters:
            board.set_char((x, y), ch.upper())
        elif ch == '[':
            board.clues = board.clues[1:] + [board.clues[0]]
        elif ch == ']':
            board.clues = [board.clues[-1]] + board.clues[:-1]
