from unittest import TestCase
from tempfile import gettempdir
from os import chmod
from os.path import join
from subprocess import run
from time import sleep

from ..compiler import Compiler, UndefinedWordException


class ChromaTest:
    
    def attempt(self, source, expect):
        src_path = join(self.tmp, "test.co")
        exec_path = join(self.tmp, f"test.{self.ext}")

        with open(src_path, "w") as f:
            f.write(source)

        try:
            compiler = Compiler().compile(self.arch, self.platform, src_path)
            assert expect == self.execute(exec_path) 
        except (UndefinedWordException) as e:
            assert False, str(e) + " [" + open(src_path).read() + "]"

    def execute(self, binary) -> str:
        raise NotImplementedError("Override me")


class SimpleEmit(ChromaTest):
    """
    See if platform has a working lit/emit implementation
    """

    def test_push_lit(self):
        self.attempt("R main G $30 emit ;", "0")

    def test_push_push_lit_lit(self):
        self.attempt("R main G $30 $31 emit emit ;", "10")


class BasicStackOperations(ChromaTest):
    """
    Some tests that the very basic stack operations are implemented correctly.
    Assumes a working "emit" operation.

    These operations are:
    dup, drop, swap, nip, lit
    """

    def test_push_lit(self):
        self.attempt("R main G $30 ;", "")

    def test_emit(self):
        self.attempt("R main G $30 emit ;", "0")

    def test_drop_emit(self):
        self.attempt("R main G $31 $30 drop emit ;", "1")

    def test_dup_lit_drop_emit(self):
        self.attempt("R main G $30 dup $31 drop emit ;", "0")

    def test_swap(self):
        self.attempt("R main G $31 $30 swap emit ;", "1")

    def test_nip(self):
        self.attempt("R main G $30 $31 $32 nip emit emit ;", "20")

    def test_stack_depth(self):
        lits = " ".join(str(i) for i in range(0x20, 0x80))
        expect = "".join(chr(i) for i in range(0x7f, 0x1f, -1))
        self.attempt(f"R main G {lits} {'emit ' * (0x60)} ;", expect)


class BasicArithmeticLogicOperations(ChromaTest):
    """
    Testing basic arithmetic and logicoperations. These are
    +, -, 1+, 1-

    and, or
    """

    def test_addition(self):
        self.attempt("R main G $30 $1 + emit ;", "1")

    def test_increment(self):
        self.attempt("R main G $30 1+ emit ;", "1")

    def test_decrement(self):
        self.attempt("R main G $31 1- emit ;", "0")

    def test_and(self):
        self.attempt("R main G $33 $31 and emit ;", "1")


class DivisionOperations(ChromaTest):
    """
    Testing /mod, /, and mod
    """

    def test_divmod(self):
        self.attempt("R main G 5 2 /mod $30 + emit $30 + emit ;", "21")

    def test_div(self):
        self.attempt("R main G 13 2 / $30 + emit ;", "6")

    def test_mod(self):
        self.attempt("R main G 11 10 mod $30 + emit", "1")


class ConditionalOperations(ChromaTest):
    """
    Testing basic conditionals
    """

    def test_if_should_drop(self):
        self.attempt("R main G $31 $30 if then emit ;", "1")

    def test_if_early_return(self):
        self.attempt("R main G $31 $30 if ; then emit ;", "")

    def test_if_should_skip(self):
        self.attempt("R main G $31 $0 if $30 then emit ;", "1")


class ForNext(ChromaTest):
    def test_simple_for(self):
        self.attempt("R main G $30 5 for dup emit 1+ next ;", "01234")


class ARegisterTests(ChromaTest):
    def test_simple_set_get(self):
        self.attempt("R main G $30 a! a emit", "0")

    def test_simple_increment(self):
        self.attempt("R main G $30 a! +a a emit", "1")

    def test_store_retrieve(self):
        self.attempt("R main P char G char a! $30 !a @a emit", "0")

    def test_store_increment_retrieve(self):
        self.attempt("R main P buf G buf a! +a $30 !a buf a! +a @a emit", "0")

    def test_increment_increment_word_retrieve(self):
        store = "buf a! 8 for +a next $30 !a"
        retrieve = "buf a! ++a @a"
        self.attempt("R main P buf G " + store + " " + retrieve + " emit", "0")

    
