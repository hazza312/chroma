from lexer import Lexer
from common import Colour, Token
from formatter import Formatter

class Compiler:
    def __init__(self, tokens, f, debug=False):
        self._tokens = tokens
        self._debug = debug
        self._depth = 0

        self._macros = {}
        self._definitions = {}
        self._variables = {}

        self._stack = []

        self._f = f
        self._sections = []

    def write_section(self, section, add):
        size = len(add)
        start = section["ptr"] - section["base"]
        end = start + size
        section["buf"].extend(bytes([0]) * (len(section["buf"]) - end))
        section["buf"][start:end] = add
        section["ptr"] += size
        
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

    def wx(self, nbytes):
        section = self._stack.pop()
        val = self._stack.pop()
        self.write_section(section, val.to_bytes(nbytes, byteorder="little", signed=val < 0))

    def macro_call_word(self, word): # yellow
        if type(word.val) == int:
            self._stack.append(word.val)

        elif word.val == "sections":
            self._sections = [
                {
                    "base": 0,
                    "buf": bytearray([]),
                    "ptr": 0
                } for _ in range(self._stack.pop())
            ]

        elif word.val == "+":
            self._stack.append(self._stack.pop() + self._stack.pop())

        elif word.val == "-":
            self._stack.append(-self._stack.pop() + self._stack.pop())

        elif word.val == "!":
            var = self._stack.pop()
            section = self._stack.pop()
            val = self._stack.pop()
            section[var] = val

        elif word.val == "i!":
            loc = self._stack.pop()
            val = self._stack.pop().to_bytes(1, byteorder="little", signed=True)[0]
            self._sections[0]["buf"][loc - self._sections[0]["base"]] = val

        elif word.val == "w8":
            self.wx(1)

        elif word.val == "w16":
            self.wx(2)

        elif word.val == "@":
            var = self._stack.pop()
            section = self._stack.pop()
            self._stack.append( section[var] )

        elif word.val == "drop":
            self._stack.pop()

        elif word.val == "dup":
            self._stack.append(self._stack[-1])

        elif word.val == "swap":
            self._stack[-1], self._stack[-2] = self._stack[-2], self._stack[-1]

        elif word.val == "section":
            self._stack.append(self._sections[self._stack.pop()])

        elif word.val in ("base", "ptr", "buf"):
            self._stack.append(word.val)

        elif word.val == "write":   
            section = self._stack.pop()
            self._f.write(section["buf"][:section["ptr"]])

        elif word.val == "padding":
            self._f.write(bytes([0]) * self._stack.pop())

        elif word.val in self._definitions:
            self._stack.append(self._definitions[word.val])

        elif word.val in self._macros:
            self._compile(self._macros[word.val])

        else:
            raise ValueError(f"unsupported #todo {word.val}")

    def compiled_word(self, word, next): # green
        consume = 0
        if word.val in self._macros:
            self._compile(self._macros[word.val])
        elif word.val in self._definitions:
            offset = (self._definitions[word.val] - self._sections[0]["ptr"] - 3).to_bytes(2, byteorder="little", signed=True)

            if next.val == ';': # tail rec
                op = self._macros["jmp"]
                consume = 1
            else:
                op = self._macros["call"]

            self._compile(op)
            self._sections[0]["ptr"] -= 2
            self.write_section(self._sections[0], offset)

        elif word.val in self._variables:
            self.lit(self._variables[word.val])        

        elif type(word.val) == int:
            self.lit(word.val)

        elif word.val[0] == '"' and word.val[-1] == '"':
            addr = self._sections[1]["ptr"] #self._compiler_vars["dp"] 
            self.write_section(self._sections[1], word.val[1:-1].encode())
            self.lit(addr)

        else:
            raise ValueError(f"{word.val} is undefined")

        return consume

    def variable_define_word(self, word): # purple
        self._variables[word.val] = self._sections[1]["ptr"]   
        self.write_section(self._sections[1], bytes([0, 0]))
        self.lit(self._variables[word.val])        

    def _compile(self, tokens):
        i = 0

        while i < len(tokens):
            curr = tokens[i]
            next = tokens[i+1] if i+1 < len(tokens) else None
            
            if self._debug and curr.colour not in (Colour.DOC, Colour.COMMENT):
                print(self._depth * "\t", curr.colour, curr.val)

            if curr.colour == Colour.MACHINE:
                self.write_section(self._sections[0], [curr.val]) # grey

            elif curr.colour == Colour.DEFINITION:
                self._definitions[curr.val] = self._sections[0]["ptr"] # red

            elif curr.colour == Colour.INLINE:
                i = self.macro_define_word(curr.val, i+1, tokens) # cyan

            elif curr.colour == Colour.EXECUTE:
                self._depth += 1
                self.macro_call_word(curr) # yellow
                self._depth -= 1

            elif curr.colour == Colour.COMPILE:
                i += self.compiled_word(curr, next) # green

            elif curr.colour == Colour.VARIABLE:
                self.variable_define_word(curr)

            i += 1


    def compile(self,):
        self._compile(self._tokens)
        self._compile(self._macros['compile'])



if __name__ == '__main__':
    import sys
    base = sys.argv[1].rsplit(".", 1)[0]
    tokens = Lexer(open(sys.argv[1])).all

    Formatter(tokens).write(open(f"{base}.html", "w"))
    Compiler(tokens, open(f"{base}.com", "wb"), True).compile()

