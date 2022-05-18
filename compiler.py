from lexer import Lexer
from common import Colour, Token
from formatter import Formatter

class Compiler:
    def __init__(self, tokens):
        self._tokens = tokens
        self._macros = {}
        self._definitions = {}
        self._variables = {}

        self._text = bytearray([0xe9, 0, 0])
        self._data = bytearray([])

        self._stack = []

        self._compiler_vars = {
            "ip": self.ip,
            "dp": self.dp,
            "ibase": 0x100,
            "dbase": 0x300             
        }

    def ibase(self):
        return self._compiler_vars["ibase"]

    def dbase(self):
        return self._compiler_vars["dbase"]

    def ip(self):
        return self.ibase() + len(self._text)

    def dp(self):
        return self.dbase() + len(self._data)


    def macro_define_word(self, name, i, tokens): # cyan
        self._macros[name] = []
        curr = tokens[i]
        while not ((curr.colour == Colour.EXECUTE and curr.val == ';') or curr.colour == Colour.INLINE):
            self._macros[name].append(curr)
            i += 1
            curr = tokens[i]
        if curr.colour == Colour.INLINE:
            i -= 1
        return i

    def lit(self, x):
        self._stack.append(x)
        self._compile(self._macros["lit"])

    def i16(self, x):
        self._text.extend(x.to_bytes(2, byteorder="little", signed=x < 0))

    def macro_call_word(self, word): # yellow
        if type(word.val) == int:
            self._stack.append(word.val)
        elif word.val == "+":
            self._stack.append(self._stack.pop() + self._stack.pop())

        elif word.val == "-":
            self._stack.append(-self._stack.pop() + self._stack.pop())

        elif word.val == "!":
            var = self._stack.pop()
            val = self._stack.pop()
            self._compiler_vars[var] = val

        elif word.val == "i!":
            loc = self._stack.pop()
            val = self._stack.pop().to_bytes(1, byteorder="little", signed=True)[0]
            self._text[loc - self.ibase()] = val

        elif word.val == "i8":
            self._text.extend(self._stack.pop().to_bytes(1, byteorder="little", signed=True))

        elif word.val == "i16":
            self.i16(self._stack.pop())

        elif word.val == "@":
            self._stack.append( self._compiler_vars[self._stack.pop()]())

        elif word.val == "drop":
            self._stack.pop()

        elif word.val == "dup":
            self._stack.append(self._stack[-1])

        elif word.val == "swap":
            self._stack[-1], self._stack[-2] = self._stack[-2], self._stack[-1]

        elif word.val in self._compiler_vars:
            self._stack.append(word.val)

        else:
            raise ValueError(f"unsupported #todo {word.val}")

    def compiled_word(self, word, next): # green
        consume = 0
        if word.val in self._macros:
            self._compile(self._macros[word.val])
        elif word.val in self._definitions:
            offset = (self._definitions[word.val] - self.ip() - 3).to_bytes(2, byteorder="little", signed=True)

            if next.val == ';': # tail rec
                op = self._macros["jmp"]
                consume = 1
            else:
                op = self._macros["call"]

            self._compile(op)
            self._text[-2:] = offset

        elif word.val in self._variables:
            self.lit(self._variables[word.val])        

        elif type(word.val) == int:
            self.lit(word.val)

        elif word.val[0] == '"' and word.val[-1] == '"':
            addr = self.dp()
            self._data.extend(word.val[1:-1].encode())
            self.lit(addr)

        else:
            raise ValueError(f"{word.val} is undefined")

        return consume

    def variable_define_word(self, word): # purple
        self._variables[word.val] = self.dp()       
        self._data.extend(bytes([0, 0]))
        self.lit(self._variables[word.val])        

    def _compile(self, tokens):
        i = 0

        while i < len(tokens):
            curr = tokens[i]
            next = tokens[i+1] if i+1 < len(tokens) else None

            if curr.colour == Colour.MACHINE:
                self._text.append(curr.val) # grey

            elif curr.colour == Colour.DEFINITION:
                self._definitions[curr.val] = self.ip() # red

            elif curr.colour == Colour.INLINE:
                i = self.macro_define_word(curr.val, i+1, tokens) # cyan

            elif curr.colour == Colour.EXECUTE:
                self.macro_call_word(curr) # yellow

            elif curr.colour == Colour.COMPILE:
                i += self.compiled_word(curr, next) # green

            elif curr.colour == Colour.VARIABLE:
                self.variable_define_word(curr)

            i += 1


    def compile(self, f):
        self._compile(self._tokens)
            

        self._text[1:3] = (self._definitions["main"] - self.ibase() - 3).to_bytes(2, byteorder="little", signed=True)
        f.write(self._text)

        f.write(bytes([0]) * (self.dbase() - (self.ibase() + len(self._text))))
        f.write(self._data)


if __name__ == '__main__':
    import sys
    base = sys.argv[1].rsplit(".", 1)[0]
    tokens = Lexer(open(sys.argv[1])).all

    Formatter(tokens).write(open(f"{base}.html", "w"))
    Compiler(tokens).compile(open(f"{base}.com", "wb"))

