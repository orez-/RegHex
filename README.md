# RegHex
:abcd: Terminal interface for hexagonal regex crosswords.

<img width="373" alt="screen shot 2017-09-30 at 3 38 42 pm" src="https://user-images.githubusercontent.com/1037028/31048875-7ce2a40e-a5f5-11e7-9cd6-50eff39f103d.png">

Notes impossible moves in red. Uses a custom regex engine to identify impossible moves.

Currently hardcoded to the regex crossword from the [2013 MIT Mystery Hunt](http://www.mit.edu/~puzzle/2013/coinheist.com/rubik/a_regular_crossword/grid.pdf).

#### To play
Clone the repo locally, then run `python3 display.py` in the cloned directory.

#### Controls
- Arrow keys to navigate the board
- Letters to enter a letter
- `[` and `]` to rotate the board
- Space or backspace to clear a letter
- Ctrl+C to end
