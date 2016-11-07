import itertools
import os.path
import random


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


def print_board(board):
    size = SIZE - 1

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
        width = size * 2 - abs(y)
        for x in range(width + 1):
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
    print_board(board)

