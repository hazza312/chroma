from unittest import TestCase
from tempfile import gettempdir
from os import chmod
from os.path import join
from subprocess import run
from time import sleep

from ..compiler import Compiler

from .test_common import *

class ARM64MacTest(
    BasicStackOperations, 
    BasicArithmeticLogicOperations,
    DivisionOperations,
    ConditionalOperations,
    ForNext,
    ARegisterTests,
    TestCase
):
    arch = "arm64"
    platform = "mac"
    ext = "out"
    tmp = gettempdir()    

    def execute(self, binary) -> str:
        chmod(binary, 0o775)
        run(['codesign', '--force', '-s', '-', binary], )
        return run(binary, timeout=1, capture_output=True).stdout.decode()

