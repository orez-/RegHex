import itertools
import os.path
import random

import get_key

SIZE = 4


def get_words():
    with open(os.path.expanduser('~/Desktop/python_sundry/dictionary.txt')) as f:
        groups = itertools.groupby(f, lambda x: x[0].lower())
        for _ in range(3):
            letter, word_group = next(groups)
            group = sorted(
                word.strip()
                for word in random.sample(list(word_group), SIZE * 2 - 1)
            )
            yield group


def print_board(board, hilite):
    size = SIZE - 1
    hx, hy = hilite

    max_width = max(
        len(word) - abs(y)
        for y, word in enumerate(board.clues[0], -size)
    )

    top = iter(board.clues[1][::-1])
    bottom = iter([''] + board.clues[2][::-1])

    # Top
    for y, word in zip(range(SIZE + 1), top):
        # 3 is the length of the space between the left words and the hex.
        print(' ' * (max_width + 3 + SIZE * 2 - y) + '/ ' * y + word)

    # Main hex part
    for y, word in enumerate(board.clues[0], -size):
        print('{:>{}}'.format(word, max_width + abs(y)), end=' ─ ')
        start = -min(y, 0) - size
        end = size - max(y, 0)
        for x in range(start, end + 1):
            if x == hx and y == hy:
                print(end='! ')
            else:
                print(end='. ')
        if y < 0:
            print('/', next(top, ''))
        elif y > 0:
            print('\\', next(bottom))
        else:
            print()

    for y, word in enumerate(bottom, -SIZE):
        # 3 is the length of the space between the left words and the hex.
        print(' ' * (max_width + 3 + SIZE * 2 + y) + '\\ ' * abs(y) + word)




class HexBoard:
    def __init__(self, clues):
        self.clues = list(clues)


if __name__ == '__main__':
    board = HexBoard(get_words())
    ch = None
    x = 0
    y = 0
    while ch != '\x03':
        print_board(board, (x, y))
        ch = get_key.getch()
        if ch == get_key.LEFT_ARROW:
            x -= 1
        elif ch == get_key.RIGHT_ARROW:
            x += 1
        elif ch == get_key.UP_ARROW:
            if y % 2:
                x += 1
            y -= 1
        elif ch == get_key.DOWN_ARROW:
            if not (y % 2):
                x -= 1
            y += 1
