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

        self._magic_dst = 0
        self._endian = "big"   
        
        self._unresolved = {"jmp": [], "call": []}

    def write_section(self, section, add):  
        section_size = len(section["buf"])   
        write_size = len(add)
        write_ptr = section["ptr"] - section["base"]
        
        if write_ptr + write_size > section_size:
            extend = write_ptr + write_size - section_size 
            section["buf"].extend(bytes([0]) * extend)
        
        section["buf"][write_ptr:write_ptr+write_size] = add
        section["ptr"] += write_size
        
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

    def write_word(self, nbytes, section):
        val = self._stack.pop()
        bytes = val.to_bytes(nbytes, byteorder=self._endian, signed=val < 0)

        if section >= 1:
            self.write_section(self._sections[section -1 ], bytes)
        else:
            self._f.write(bytes)
        
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

        elif word.val == "magic!":
            self._magic_dst = self._stack.pop() - 1

        elif word.val == "+":
            self._stack.append(self._stack.pop() + self._stack.pop())

        elif word.val == "*":
            self._stack.append(self._stack.pop() * self._stack.pop())

        elif word.val == "-":
            self._stack.append(-self._stack.pop() + self._stack.pop())

        elif word.val == "!":
            var = self._stack.pop()
            section = self._stack.pop()
            val = self._stack.pop()
            self._sections[section - 1][var] = val
            
        elif word.val in ('i8!', 'i16!', 'i32!'):
            bytes = int(word.val[1:-1]) // 8
            loc = self._stack.pop()
            val = self._stack.pop().to_bytes(bytes, byteorder=self._endian, signed=True)
            start = loc - self._sections[0]["base"]
            self._sections[0]["buf"][start:start+bytes] = val

        elif word.val in ("w8", "w16", "w32", "w64"):
            self.write_word(int(word.val[1:]) // 8, self._stack.pop())

        elif word.val == "@":
            var = self._stack.pop()
            section = self._stack.pop() - 1
            self._stack.append( self._sections[section][var] )

        elif word.val == "drop":
            self._stack.pop()

        elif word.val == "dup":
            self._stack.append(self._stack[-1])

        elif word.val == "len":
            self._stack.append(len(self._stack.pop()))

        elif word.val == ".S":
            print("magic=", self._magic_dst, self._stack, self._sections)

        elif word.val == "cpy":
            dst = self._stack.pop()
            string = self._stack.pop()
            self.write_section(self._sections[dst - 1], string.encode())

        elif word.val == "swap":
            self._stack[-1], self._stack[-2] = self._stack[-2], self._stack[-1]

        elif word.val == "section":
            self._stack.append(self._sections[self._stack.pop() - 1])

        elif word.val in ("base", "ptr", "buf", "little", "big"):
            self._stack.append(word.val)

        elif word.val == "endian":
            self._endian = self._stack.pop()

        elif word.val == "write": 
            section = self._sections[self._stack.pop() - 1]
            self._f.write(section["buf"][:section["ptr"]])

        elif word.val == "padding":
            self._f.write(bytes([0]) * self._stack.pop())

        elif word.val[0] == '"' and word.val[-1] == '"':
            self._stack.append(word.val[1:-1])

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

        elif word.val in self._variables:
            self.lit(self._variables[word.val])        

        elif type(word.val) == int:
            self.lit(word.val)

        elif word.val[0] == '"' and word.val[-1] == '"':
            self._stack.append(word.val[1:-1])
            self._compile(self._macros["str"])
            
        else:
        	if next.val == ';':
        		op = "jmp"
        		consume = 1
        	else:
        		op = "call"
        		consume = 0
        
        	if word.val not in self._definitions:
        		target = 0
        		self._unresolved[op].append((self._sections[0]["ptr"], word.val))
        	
        	else:
        		target = self._definitions[word.val]
        	
        	self._stack.append(target)
        	self._compile(self._macros[op])       

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
                self._stack.append(curr.val)
                self.write_word(1, self._magic_dst + 1)


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

    def compile(self):
        self._compile(self._tokens)
        end = self._sections[0]['ptr']
        
        for (op, unresolveds) in self._unresolved.items():
             for (loc, target) in unresolveds:
                if target not in self._definitions:
                    raise ValueError(f"{op} to {target} remains unresolved")
        		
                self._sections[0]['ptr'] = loc
                self._stack.append(self._definitions[target])
                self._compile(self._macros[op])
        
        self._sections[0]['ptr'] = end
        self._compile(self._macros['compile'])


if __name__ == '__main__':
    import sys
    base = sys.argv[1].rsplit(".", 1)[0]
    tokens = Lexer(open(sys.argv[1])).all

    Formatter(tokens).write(open(f"{base}.html", "w"))
    Compiler(tokens, open(f"{base}.out", "wb"), False).compile()

