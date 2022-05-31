from enum import Enum
from dataclasses import dataclass
from typing import Any 

class Colour(Enum):
    COMMENT = "W"
    MACHINE = "M"
    DEFINITION = "R"
    INLINE = "I"
    EXECUTE = "Y"
    COMPILE = "G"
    VARIABLE = "P"
    REFERENCE = "O"
    DOC = "\n"
    
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
