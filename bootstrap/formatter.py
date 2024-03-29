from .common import Colour, Token
from .lexer import Lexer
from random import randint

class Formatter:
    def __init__(self, tokens):
        self._tokens = tokens

    def write(self, f):
        colour = f"rgb({randint(0, 255)}, {randint(0, 255)}, {randint(0, 255)})"
        f.write(f'<html style="background: {colour}"><body style="padding: 25px; margin: 25px; background: #333; font-family: monospace">')
        for token in self._tokens:
            if token.val == "\n":
                f.write("<br>")
            else:
                hex_colour = token.colour.to_hex
                val = hex(token.val)[2:].rjust(2, '0') if type(token.val) == int else token.val 
                f.write(f'<span style="color: {hex_colour}">{val}</span> ')
        f.write('</body></html>')


if __name__ == '__main__':
    import sys
    source = sys.argv[1] 
    Formatter(Lexer(open(source)).all).write(open(f"{source}.html", "w"))

