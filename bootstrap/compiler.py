#!/usr/bin/python3.9

from os.path import dirname, join, abspath, splitext

from .lexer import Lexer
from .common import Colour, Token
from .formatter import Formatter

class UndefinedWordException(Exception):
    def __init__(self, word_type, word, ref_type=None, branch_type=None, *args, **kwargs):
        self.word_type = word_type
        self.word = word
        self.ref_type = ref_type
        self.branch_type = branch_type
        super(*args, **kwargs)
    
    def __str__(self):
        return f"'{self.word}' is undefined "


class Compiler:
    def __init__(self, arch, platform, debug=False):
        self._arch = arch
        self._platform = platform
        self._debug = debug
        self._depth = 0

        self._here = dirname(__file__)

        self._macros = {}
        self._definitions = {}
        self._variables = {}

        self._stack = []
        self._rstack = []

        self._f = None
        self._sections = []

        self._magic_dst = 0
        self._endian = "big"   
        self._ext = ""
        
        self._last_green = None
        
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
        
    def alit(self, x):
        self._stack.append(x)
        self._compile(self._macros["alit"])

    def write_word(self, nbytes, section):
        val = self._stack.pop()
        bytes = val.to_bytes(nbytes, byteorder=self._endian, signed=val < 0)
        
        if section >= 1:
            self.write_section(self._sections[section -1 ], bytes)
        else:
            self._f.write(bytes)
        
    def macro_call_word(self, word): # yellow   
        if type(word) == int:
            self._stack.append(word)

        elif word == "sections":
            self._sections = [
                {
                    "base": 0,
                    "buf": bytearray([]),
                    "ptr": 0
                } for _ in range(self._stack.pop())
            ]

        elif word == "magic!":
            self._magic_dst = self._stack.pop() - 1
            
        elif word == "ext":
            self._ext = self._stack.pop()

        elif word == "+":
            self._stack.append(self._stack.pop() + self._stack.pop())

        elif word == "*":
            self._stack.append(self._stack.pop() * self._stack.pop())

        elif word == "-":
            self._stack.append(-self._stack.pop() + self._stack.pop())
            
        elif word == "and":
            self._stack.append(self._stack.pop() & self._stack.pop())

        elif word == "or":
            self._stack.append(self._stack.pop() | self._stack.pop())

        elif word == "shr":
            shift = self._stack.pop()
            num = self._stack.pop()
            self._stack.append(num >> shift)

        elif word == "shl":
            shift = self._stack.pop()
            num = self._stack.pop()
            self._stack.append(num << shift)

        elif word == "!":
            var = self._stack.pop()
            section = self._stack.pop()
            val = self._stack.pop()
            self._sections[section - 1][var] = val
            
        elif word in ('i8!', 'i16!', 'i32!'):
            bytes = int(word[1:-1]) // 8
            loc = self._stack.pop()
            val = self._stack.pop()
            val = val.to_bytes(bytes, byteorder=self._endian, signed=val < 0)
            start = loc - self._sections[0]["base"]
            self._sections[0]["buf"][start:start+bytes] = val

        elif word in ("w8", "w16", "w32", "w64"):
            self.write_word(int(word[1:]) // 8, self._stack.pop())

        elif word == "@":
            var = self._stack.pop()
            section = self._stack.pop() - 1
            self._stack.append( self._sections[section][var] )

        elif word == "drop":
            self._stack.pop()

        elif word == "dup":
            self._stack.append(self._stack[-1])

        elif word == "len":
            self._stack.append(len(self._stack.pop()))

        elif word == ".S":
            print("magic=", self._magic_dst, self._stack)

        elif word == "cpy":
            dst = self._stack.pop()
            string = self._stack.pop()
            self.write_section(self._sections[dst - 1], string.encode())

        elif word == "swap":
            self._stack[-1], self._stack[-2] = self._stack[-2], self._stack[-1]

        elif word == "section":
            self._stack.append(self._sections[self._stack.pop() - 1])

        elif word in ("base", "ptr", "buf", "little", "big"):
            self._stack.append(word)

        elif word == "endian":
            self._endian = self._stack.pop()

        elif word == "write": 
            section = self._sections[self._stack.pop() - 1]
            self._f.write(section["buf"][:section["ptr"]])

        elif word == "padding":
            self._f.write(bytearray([0]) * self._stack.pop())

        elif word == "include":
            self._compile(join(self._here, "..", "lib", self._stack.pop() + ".co"))
            
        elif word == "magic!":
            self._magic_dst = self._stack.pop() - 1
            
        elif word == ">r":
            self._rstack.append(self._stack.pop())
        
        elif word == "r>":
            self._stack.append(self._rstack.pop())

        elif word[0] == '"' and word[-1] == '"':
            self._stack.append(word[1:-1])

        elif word in self._definitions:
            self._stack.append(self._definitions[word])

        elif word in self._macros:
            self._depth += 1
            self._compile(self._macros[word])
            self._depth -= 1
 
        elif word in self._variables:
            self._stack.append(self._variables[word])

        else:
            raise UndefinedWordException("macro", word, "back")

    def compiled_word(self, word, next): # green
        consume = 0
        if word.val in self._macros:
            self._depth += 1
            self._compile(self._macros[word.val])
            self._depth -= 1

        elif word.val in self._variables:
            cmd = self.alit if 'alit' in self._macros else self.lit
            cmd(self._variables[word.val])        

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

    def _compile(self, f):
        tokens = Lexer(open(f)).all if type(f) != list else f
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
                self.macro_call_word(curr.val) # yellow
                self._depth -= 1

            elif curr.colour == Colour.COMPILE:
                i += self.compiled_word(curr, next) # green
                self._last_green = tokens[i].val

            elif curr.colour == Colour.VARIABLE:
                self.variable_define_word(curr)

            i += 1

    def compile(self, f):
        base, _ = splitext(abspath(f))
        if self._arch != "raw":
            for path in sys_includes(self._arch, self._platform):
                self._compile(path)

            self._compile(join(self._here, "..", "lib", "core.co"))
        self._compile(f) 
        self.tape_out(base)
        
    def make_listing(self, path):  
        with open(path, "w") as f:
            f.write("Code labels\n")

            for name, addr in self._definitions.items():
                f.write(f"{name:20}{hex(addr)}\n")

            f.write("Data labels\n")
            for name, addr in self._variables.items():
                f.write(f"{name:20}{hex(addr)}\n")

        
    def tape_out(self, output):
        self._f = open(f"{output}.{self._ext}", "wb")
        end = self._sections[0]['ptr']

        for (op, unresolveds) in self._unresolved.items():
             for (loc, target) in unresolveds:
                if target not in self._definitions:
                    raise UndefinedWordException("user",  target, "back", op)

                self._sections[0]['ptr'] = loc
                self._stack.append(self._definitions[target])
                self._compile(self._macros[op])
        
        self._sections[0]['ptr'] = end
        self._compile(self._macros['compile'])
        self.make_listing(f"{output}.{self._ext}.lst")

def sys_includes(arch, platform):
    here = dirname(__file__)
    return [
        join(here, "..", "arch", arch, platform, f"{platform}.co"),
        join(here, "..", "arch", arch, f"{arch}.co"),
        join(here, "..", "lib", arch, platform, "base.co")
    ]


if __name__ == '__main__':
    import sys
    
    arch, platform = sys.argv[1].split("/")
    source = sys.argv[2] 
    tokens = []
    if (len(sys.argv) > 3 and sys.argv[3] == 'sys' and arch != 'raw'):
        new_lines = [Token(Colour.DOC, '\n')] * 2
        for path in sys_includes(arch, platform):
            tokens.extend(new_lines + [Token(Colour.COMMENT, path.center(100, '-'))] + new_lines)
            tokens.extend(Lexer(open(path)).all)
        
        tokens.extend(new_lines + [Token(Colour.COMMENT, source.center(100, '-'))] + new_lines)
    
    tokens.extend(Lexer(open(source)).all)
    
    Formatter(tokens).write(open(f"{source}.html", "w"))    
    Compiler(arch, platform, debug=False).compile(source)
