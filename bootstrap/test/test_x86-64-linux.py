from unittest import TestCase
from tempfile import gettempdir
from os import chmod
from os.path import join
from subprocess import run
from time import sleep

from ..compiler import Compiler

from .test_common import *

class X8664Test(
    BasicStackOperations, 
    BasicArithmeticLogicOperations,
    ConditionalOperations,
    ForNext,
    TestCase
):
    arch = "x86-64"
    platform = "Linux"
    ext = "out"
    tmp = gettempdir()    

    def attempt(self, source, expect):
        src_path = join(self.tmp, "test.co")
        exec_path = join(self.tmp, f"test.{self.ext}")

        with open(src_path, "w") as f:
            f.write(source)

        compiler = Compiler().compile(self.arch, self.platform, src_path)

        assert expect == self.execute(exec_path) 


    def execute(self, binary) -> str:
        chmod(binary, 0o775)
        return run(binary, timeout=1, capture_output=True).stdout.decode()

