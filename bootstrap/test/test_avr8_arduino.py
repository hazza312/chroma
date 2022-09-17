from unittest import TestCase
from tempfile import gettempdir
from os import chmod
from os.path import join
from subprocess import run, TimeoutExpired
from time import sleep

from ..compiler import Compiler

from .test_common import *


class ArduinoTest(
    SimpleEmit,
    BasicStackOperations,
    BasicArithmeticLogicOperations,
    ConditionalOperations,
    ForNext,
    TestCase
):
    arch = "avr8"
    platform = "Arduino"
    ext = "bin" 
    tmp = gettempdir() 

    def execute(self, binary) -> str:
        try:
            run(["/home/harry/apps/qemu/qemu-system-avr", 
                "-machine", "uno",
                "-bios", binary, 
                "-nographic"],
                timeout=0.2,
                capture_output=True)
        except TimeoutExpired as e:
            return e.stdout.decode()
