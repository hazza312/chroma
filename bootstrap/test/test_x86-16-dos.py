from unittest import TestCase
from tempfile import gettempdir
from os import chmod
from os.path import join, basepath
from subprocess import run
from time import sleep

from ..compiler import Compiler

from .test_suites import CompleteTestSuite

class DOSTest(CompleteTestSuite, TestCase):
    arch = "x86-16"
    platform = "DOS"
    ext = "com"
    tmp = gettempdir() 

    def execute(self, binary) -> str:
        bin = basepath(binary)
        output = bin.split(".")[0].upper()
        
        run(["dosbox", 
            "-c", f"mount c {self.tmp}",
            "-c", f"c:",
            "-c", f"{bin} > {output}",
            "-c", "exit"], timeout=2, env={"SDL_VIDEODRIVER": "dummy"})

        with open(join(self.tmp, output)) as f:
            return f.read() 
    
