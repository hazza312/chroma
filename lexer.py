from common import Colour, Token

class Lexer:
    def __init__(self, io):
        self._io = io
        self._colour = None

    def _lex(self):
        for line in self._io.read().splitlines():
            for word in line.split():
                try:
                    self._colour = Colour(word)
                    continue
                except ValueError:
                    pass

                if self._colour == Colour.MACHINE:
                    val = int(word, 16)
                elif word.isdigit():
                    val = int(word)
                elif word.startswith('$'):
                    val = int(word[1:], 16)
                else:
                    val = word

                yield Token(self._colour, val)

            yield Token(Colour.DOC, "\n")

    @property
    def all(self):
        return list(iter(self._lex()))
