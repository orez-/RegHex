import collections
import contextlib
import re
import traceback

ANY_CHR = " "


class RegEx(object):
    pass


class Empty(RegEx):
    def match(self, string, index):
        del string
        yield index, ''

    def __repr__(self):
        return "Empty()"

RegEx.empty = Empty()


class Statement(RegEx):
    def __init__(self, regex):
        self._regex = regex

    def match(self, string):
        for m, word in self._regex.match(string, 0):
            del word
            if m == len(string):
                return True
        return False

    def __repr__(self):
        return "Statement( {!r} )".format(self._regex)


class Choice(RegEx):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def match(self, string, index):
        yield from self.left.match(string, index)
        yield from self.right.match(string, index)

    def __repr__(self):
        return "Choice( {!r}, {!r} )".format(self.left, self.right)


class Sequence(RegEx):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def match(self, string, index):
        for i, one in self.left.match(string, index):
            for j, two in self.right.match(string, i):
                yield j, one + two

    def __repr__(self):
        return "Sequence( {!r}, {!r} )".format(self.left, self.right)


class Repetition(RegEx):
    def __init__(self, internal, at_least_one):
        self._internal = internal
        self._at_least_one = at_least_one

    def match(self, string, index, *, skip_num_check=False):
        zero_width = False
        for i, start in self._internal.match(string, index):
            if i != index:
                for j, more in self.match(string, i, skip_num_check=True):
                    yield j, start + more
            else:
                zero_width = True

        if skip_num_check or not self._at_least_one or zero_width:
            yield index, ''

    def __repr__(self):
        return "Repetition{}( {!r} )".format(
            '+' if self._at_least_one else '*',
            self._internal,
        )


class Symbol(RegEx):
    def __init__(self, symbol):
        self._symbol = symbol

    def __repr__(self):
        return "Symbol( {!r} )".format(self._symbol)

    def match(self, string, index):
        for i, expected in enumerate(self._symbol):
            try:
                char = string[index + i]
            except IndexError:
                return

            if expected == '.':
                continue
            if char not in {ANY_CHR, expected}:
                return
        yield index + len(self._symbol), string[index:index + len(self._symbol)]


class Bracket(RegEx):
    def __init__(self, chars):
        self._chars = chars

    def __repr__(self):
        return "Bracket( {!r} )".format(self._chars)

    def match(self, string, index):
        # shut up
        try:
            if string[index] == ANY_CHR or re.match(r"[{}]".format(self._chars), string[index]):
                yield index + 1, string[index]
        except IndexError:
            pass


class Backref(RegEx):
    def __init__(self, capture):
        self._capture = capture

    def __repr__(self):
        return "Backref()"

    def match(self, string, index):
        yield from self._capture.ref_match(string, index)


class Capture(RegEx):
    def __init__(self, regex):
        self._regex = regex
        self._shapes = collections.deque()

    def __repr__(self):
        return "Capture( {!r} )".format(self._regex)

    @staticmethod
    def _combine(str1, str2):
        """
        Combine two strings, respecting ANY_CHR.
        If the strings are incompatible, return None
        """
        if len(str1) != len(str2):
            return

        new_word = collections.deque()
        for a, b in zip(str1, str2):
            if a == b or b == ANY_CHR:
                new_word.append(a)
            elif a == ANY_CHR:
                new_word.append(b)
            else:
                return
        return ''.join(new_word)

    def match(self, string, index):
        yield from self._match(string, index)

    def _match(self, string, index, offset=0):
        for i, word in self._regex.match(string, index):
            with self._push(word):
                yield i + offset, word

    def ref_match(self, string, index):
        shape = self._shapes[-1]
        value = string[index: index + len(shape)]
        string = self._combine(shape, value)
        if string is None:
            return
        yield from self._match(string, 0, index)

    @contextlib.contextmanager
    def _push(self, value):
        self._shapes.append(value)
        yield
        self._shapes.pop()


class Optional(RegEx):
    def __init__(self, regex):
        self._regex = regex

    def __repr__(self):
        return "Optional( {!r} )".format(self._regex)

    def match(self, string, index):
        yield from self._regex.match(string, index)
        yield index, ''

# ---


class RegExParser:
    def __init__(self, input_):
        self._input = input_
        self._captures = []

    def parse(self):
        self._ptr = 0
        return self._statement()

    # Recursive descent parsing internals.

    def _peek(self):
        return self._input[self._ptr]

    def _eat(self, character):
        if self._peek() == character:
            self._ptr += 1
        else:
            raise Exception("Expected: {}; got: {}".format(character, self._peek()))

    def _next(self):
        c = self._peek()
        self._eat(c)
        return c

    def _more(self):
        return self._ptr < len(self._input)

    # Regular expression term types.

    def _statement(self):
        return Statement(self._regex())

    def _regex(self):
        term = self._term()

        if self._more() and self._peek() == '|':
            self._eat('|')
            regex = self._regex()
            return Choice(term, regex)
        return term

    def _term(self):
        factor = RegEx.empty

        while self._more() and self._peek() != ')' and self._peek() != '|':
            nextFactor = self._factor()
            factor = Sequence(factor, nextFactor)

        return factor

    def _factor(self):
        base = self._base()

        while self._more() and self._peek() == '*':
            self._eat('*')
            base = Repetition(base, False)

        while self._more() and self._peek() == '+':
            self._eat('+')
            base = Repetition(base, True)

        while self._more() and self._peek() == '?':
            self._eat('?')
            base = Optional(base)

        return base

    def _bracket(self):
        agg = []
        while self._more() and self._peek() != ']':
            agg.append(self._next())
        return Bracket(''.join(agg))

    def _base(self):
        peek = self._peek()
        if peek == '(':
            self._eat('(')
            r = self._regex()
            self._eat(')')
            capture = Capture(r)
            self._captures.append(capture)
            return capture
        if peek == '[':
            self._eat('[')
            r = self._bracket()
            self._eat(']')
            return r
        if peek == '\\':
            self._eat('\\')
            num = int(self._next())
            if num > len(self._captures) or num < 1:
                raise Exception("invalid group reference {}".format(num))
            return Backref(self._captures[num - 1])
        return Symbol(self._next())


# class RegEx(object):
#     def match(self, string):
#         raise NotImplementedError


# class Statement(RegEx):
#     """
#     < statement >  ::= ^< regex >$
#     """
#     def __init__(self, regex):
#         self._regex = regex

#     def match(self, string):
#         return self._regex.match(string)


# class Base(RegEx):
#     """
#     < term > ::= [a-z]+
#     """
#     def __init__(self, string):
#         self._literal = string

#     def match(self, string):
#         if len(self._literal) > len(string):
#             return False
#         return all(c in [a, ANY_CHR] for a, c in zip(self._literal, string))


def compile_re(regex):
    return RegExParser(regex).parse()


# ===

if __name__ == '__main__':
    af = '\x1b[38;5;{}m'.format
    clear = '\x1b[0m'

    def match(regex, string, expected=True):
        msg = "{{}}{!r} {}~ {!r}: {{}}!".format(regex, "=" if expected else "≠", string).format
        try:
            compiled_regex = compile_re(regex)
            if compiled_regex.match(string) == expected:
                print(msg(af(2), "Success"), end='')
                print(clear)
            else:
                print(msg(af(3), "Failure"), end='')
                print(clear)
        except Exception:
            print(msg(af(1), "Error"))
            traceback.print_exc()
            print(clear)

    def run_tests():
        match(r"abc", "abc")
        match(r"abc", "def", False)
        match(r"abc", "   ")
        match(r"abc", "a  ")
        match(r"abc", " b ")
        match(r"abc", "  c")
        match(r"abc", " e ", False)
        match(r"abcd", "abc", False)
        match(r"(abc)", "abc")

        match(r"a.c", "ab ")
        match(r"a.c", "a c")

        match(r"abc|def", "abc")
        match(r"abc|def", "def")
        match(r"abc|def", "  c")
        match(r"abc|def", "d  ")
        match(r"abc|def", "abf", False)
        match(r"abc|def", "a f", False)

        match(r"a[nuts]c", "a c")
        match(r"a[nuts]c", "at ")

        match(r"a[n-s]c", "a c")
        match(r"a[n-s]c", " pc")

        match(r"a*c", "aac")
        match(r"a*c", "a c")
        match(r"a*c", "a  ")
        match(r"a*c", " ac")
        match(r"a*c", "  c")
        match(r"a*c", "   ")
        match(r"()*abc", "   ")
        match(r"()+abc", "   ")

        match(r"[nuts]*", "   ")
        match(r"[nuts]*", "stu")
        match(r"[nuts]+", "tun")
        match(r"[abc]*[nuts]+yz", "tyz")
        match(r"[abc]*[nuts]+yz", "ayz", False)
        match(r"[^nuts]*", "abc")
        match(r"([^mc]|mm|cc)*", "  f")
        match(r"([^mc]|mm|cc)*", " fm", False)
        match(r"([^mc]|mm)*", "xyz")

        match(r"([ab])\1*", "aaaaa")
        match(r"([ab])\1*", "bbbbb")
        match(r"([ab])\1*", "babab", False)
        match(r"([ab])\1*", "b b b")
        match(r"([ab])\1*", "b a b", False)
        match(r"([ab])\1*", " a b ", False)
        match(r"([ab])\1*", "  c  ", False)
        match(r"([ab]+)q\1", "   qab", False)
        match(r"([ab]+)q\1", " b qa a")
        match(r"([ab]+)\1", " ba ")
        match(r"([ab]+)\1", "   ", False)
        match(r"(ab|cd)\1", "a  d", False)
        match(r"(ab|cd)\1+", "a  d  ", False)

        match(r"a?b?", "a")
        match(r"a?b?", "b")
        match(r"a?b?", "c", False)
        match(r"a?", " ")

    run_tests()
