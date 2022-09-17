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
    ARegisterTests,
    TestCase
):
    arch = "x86-64"
    platform = "Linux"
    ext = "out"
    tmp = gettempdir()    

    def execute(self, binary) -> str:
        chmod(binary, 0o775)
        return run(binary, timeout=1, capture_output=True).stdout.decode()

