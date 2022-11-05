from unittest import TestCase
from tempfile import gettempdir
from os import chmod
from os.path import join
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
        run(["dosbox", 
            "-c", f"mount c {self.tmp}",
            "-c", f"c:",
            "-c", f"test{self.test_no}.com > OUT{self.test_no}.TXT",
            "-c", "exit"], timeout=2, env={"SDL_VIDEODRIVER": "dummy"})

        with open(join(self.tmp, f"OUT{self.test_no}.TXT")) as f:
            return f.read() 
    
