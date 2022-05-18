from common import Colour, Token

class Formatter:
    def __init__(self, tokens):
        self._tokens = tokens

    def write(self, f):
        f.write('<html><body style="background: black; font-family: monospace"><pre>')
        for token in self._tokens:
            if token.val == "\n":
                f.write("<br>")
            else:
                hex_colour = token.colour.to_hex
                val = hex(token.val)[2:].rjust(2, '0') if token.colour == Colour.MACHINE else token.val 
                f.write(f'<span title="{token.colour.description}" style="background: black; color: {hex_colour}">{val}</span> ')
        f.write('</pre></body></html>')

