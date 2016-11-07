import sys

UP_ARROW = object()
LEFT_ARROW = object()
RIGHT_ARROW = object()
DOWN_ARROW = object()


try:
    import termios
    import tty
except ImportError:
    # Probably Windows.
    try:
        import msvcrt
    except ImportError:
        # FIXME what to do on other platforms?
        # Just give up here.
        raise ImportError('getch not available')
    else:
        _windows_keys = {
            '\xe0H': UP_ARROW,
            '\xe0K': LEFT_ARROW,
            '\xe0P': DOWN_ARROW,
            '\xe0M': RIGHT_ARROW,
        }

        def getch():
            ch = msvcrt.getwch()
            if ch in ('\x00', '\xe0'):
                ch += msvcrt.getwch()
                return _windows_keys.get(ch, ch)
            return ch
else:
    _unix_keys = {
        '\x1b[A': UP_ARROW,
        '\x1b[D': LEFT_ARROW,
        '\x1b[B': DOWN_ARROW,
        '\x1b[C': RIGHT_ARROW,
    }

    def getch():
        """getch() -> key character

        Read a single keypress from stdin and return the resulting character.
        Nothing is echoed to the console. This call will block if a keypress
        is not already available, but will not wait for Enter to be pressed.

        If the pressed key was a modifier key, nothing will be detected; if
        it were a special function key, it may return the first character of
        of an escape sequence, leaving additional characters in the buffer.
        """
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # arrow key control character
                ch += sys.stdin.read(2)
                return _unix_keys.get(ch, ch)

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
