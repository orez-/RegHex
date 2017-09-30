import enum
import string

import get_key
import regish


af = '\x1b[38;5;{}m'
ab = '\x1b[48;5;{}m'
clear = '\x1b[0m'


def get_original_clues():
    return [
        [
            r'.*H.*H.*',
            r'(DI|NS|TH|OM)*',
            r'F.*[AO].*[AO].*',
            r'(O|RHH|MM)*',
            r'.*',
            r'C*MC(CCC|MM)*',
            r'[^C]*[^R]*III.*',
            r'(...?)\1*',
            r'([^X]|XCC)*',
            r'(RR|HHH)*.?',
            r'N.*X.X.X.*E',
            r'R*D*M*',
            r'.(C|HH)*',
        ],
        [
            r'.*SE.*UE.*',
            r'.*LR.*RL.*',
            r'.*OXR.*',
            r'([^EMC]|EM)*',
            r'(HHX|[^HX])*',
            r'.*PRR.*DDC.*',
            r'.*',
            r'[AM]*CM(RC)*R?',
            r'([^MC]|MM|CC)*',
            r'(E|CR|MN)*',
            r'P+(..)\1.*',
            r'[CHMNOR]*I[CHMNOR]*',
            r'(ND|ET|IN)[^X]*',
        ],
        [
            r'.*G.*V.*H.*',
            r'[CR]*',
            r'.*XEXM*',
            r'.*DD.*CCM.*',
            r'.*XHCR.*X.*',
            r'.*(.)(.)(.)(.)\4\3\2\1.*',
            r'.*(IN|SE|HI)',
            r'[^C]*MMM[^C]*',
            r'.*(.)C\1X\1.*',
            r'[CEIMU]*OH[AEMOR]*',
            r'(RX|[^R])*',
            r'[^M]*M[^M]*',
            r'(S|MM|HHH)*',
        ],
    ]


def start_of_row(y, size):
    return -min(y, 0) - size


def get_color(status, bg=False):
    color = ab if bg else af
    if status == RowStatus.valid:
        return ab.format(7) + af.format(0) if bg else ''
    if status == RowStatus.invalid:
        return color.format(161)
    if status == RowStatus.finished:
        return color.format(244)


def print_board(board, hilite):
    SIZE = board.size
    size = SIZE - 1
    hx, hy, hz = coordinate(*hilite)

    max_width = max(
        len(clue.clue) - abs(y)
        for y, clue in enumerate(board.clues[0], -size)
    )

    top = iter(board.clues[1][::-1] + [''])
    bottom = iter([''] + board.clues[2][::-1])

    # Top
    for y, clue in zip(range(SIZE + 1), top):
        color = get_color(clue.status, -y + size == hz) if clue else ''
        # 3 is the length of the space between the left words and the hex.
        print(' ' * (max_width + 3 + SIZE * 2 - y), '/ ' * y, color, str(clue), clear, sep='')

    # Main hex part
    for y, clue in enumerate(board.clues[0], -size):
        color = get_color(clue.status, hy == y) if clue else ''
        print(
            ' ' * (max_width + abs(y) - len(str(clue))), color, str(clue), clear,
            sep='',
            end=' - ',
        )
        start = start_of_row(y, size)
        end = size - max(y, 0)
        for x, letter in enumerate(clue.text, start):
            color = get_color(RowStatus.valid, x == hx and y == hy)
            print(color, letter or '.', clear, sep='', end=' ')
        if y < 0:
            clue = next(top)
            # two lines above the end of the row
            color = get_color(clue.status, -end - y - 2 == hz) if clue else ''
            print('/ ', color, clue, clear, sep='')
        elif y > 0:
            clue = next(bottom)
            # two lines below the end of the row
            color = get_color(clue.status, end + 2 == hx) if clue else ''
            print('\\ ', color, clue, clear, sep='')
        else:
            print()

    for y, clue in enumerate(bottom, -SIZE):
        color = get_color(clue.status, -y - size == hx) if clue else ''
        # 3 is the length of the space between the left words and the hex.
        print(' ' * (max_width + 3 + SIZE * 2 + y), '\\ ' * abs(y), color, str(clue), clear, sep='')
    print()


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


class RowStatus(enum.Enum):
    valid = 1
    invalid = 2
    finished = 3


class ClueRow:
    def __init__(self, clue, length):
        self.clue = clue
        self.re_clue = regish.compile_re(clue)
        self.text = [None] * length
        self.status = RowStatus.valid

        self.validate()

    @property
    def as_text(self):
        return ''.join(letter or ' ' for letter in self.text)

    def validate(self):
        match = self.re_clue.match(self.as_text)

        done = None not in self.text
        if not match:
            self.status = RowStatus.invalid
        elif done:
            self.status = RowStatus.finished
        else:
            self.status = RowStatus.valid

    def set_char(self, pos, char):
        self.text[pos] = char
        self.validate()

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


def run_cli():
    SIZE = 7
    words = get_original_clues()

    board = HexBoard(words, SIZE)

    x = 0
    y = 0
    ch = None
    while ch != '\x03':
        print("\033c")
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
        elif ch in (' ', '\x7f'):
            board.set_char((x, y), None)
        elif ch == '[':
            board.clues = board.clues[1:] + [board.clues[0]]
        elif ch == ']':
            board.clues = [board.clues[-1]] + board.clues[:-1]


if __name__ == '__main__':
    run_cli()
