from enum import IntEnum
from dataclasses import dataclass
from typing import Any 

class Colour(IntEnum):
    COMMENT = 0
    MACHINE = 1
    DEFINITION = 2
    INLINE = 3
    EXECUTE = 4
    COMPILE = 5
    VARIABLE = 6
    REFERENCE = 7
    DOC = 8

    @classmethod
    def parse(cls, s):
        return {
            'W': cls.COMMENT,
            'M': cls.MACHINE,
            'R': cls.DEFINITION,
            'I': cls.INLINE,
            'Y': cls.EXECUTE,
            'G': cls.COMPILE,
            'P': cls.VARIABLE,
            'O': cls.REFERENCE
        
        }.get(s.upper(), None)
    
    @property
    def to_hex(self):
        return {
            self.COMMENT: "#fff",
            self.MACHINE: "#aaaaaa",
            self.DEFINITION: "#ff0000",
            self.INLINE: "#00FFFF",
            self.EXECUTE: "#FFFF00",
            self.COMPILE: "#00FF7F",
            self.VARIABLE: "#FF00FF",
            self.REFERENCE: "#fff",
            self.DOC: "#fff"
        }[self]

    @property
    def description(self):
        return {
            self.COMMENT: "comment",
            self.MACHINE: "machine code",
            self.DEFINITION: "word definition",
            self.INLINE: "macro definition",
            self.EXECUTE: "macro execution",
            self.COMPILE: "compiled call, word, literal",
            self.VARIABLE: "variable declaration",
            self.REFERENCE: "-",
            self.DOC: "-"
        }[self]


@dataclass
class Token:
    colour: Colour
    val: Any
