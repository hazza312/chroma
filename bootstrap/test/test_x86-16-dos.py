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
        run(["/opt/homebrew/bin/dosbox", 
            "-c", f"mount c {self.tmp}",
            "-c", f"c:",
            "-c", "test.com > OUT.TXT",
            "-c", "exit"], timeout=2, env={"SDL_VIDEODRIVER": "dummy"})

        with open(join(self.tmp, "OUT.TXT")) as f:
            return f.read() 
    
