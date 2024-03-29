from unittest import TestCase
from tempfile import gettempdir
from os import chmod
from os.path import join
from subprocess import run
from time import sleep

from ..compiler import Compiler, UndefinedWordException


class ChromaTest:
    
    def attempt(self, source, expect):
        id = hash(source) % 10000
        src_path = join(self.tmp, f"test{id}.co")
        exec_path = join(self.tmp, f"test{id}.{self.ext}")

        with open(src_path, "w") as f:
            f.write(source)

        try:
            compiler = Compiler(self.arch, self.platform).compile(src_path)
            assert expect == self.execute(exec_path) 
        except (Exception) as e:
            assert False, str(e) + " [" + open(src_path).read() + "]"

    def execute(self, binary) -> str:
        raise NotImplementedError("Override me")
    
    
class SimpleEmit(ChromaTest):
    """
    See if platform has a working lit/emit implementation.
    
    Operations:
    lit, emit
    """

    def test_push_lit(self):
        self.attempt("R main G $30 ;", "")

    def test_emit(self):
        self.attempt("R main G $30 emit ;", "0")

    def test_push_push_lit_lit(self):
        self.attempt("R main G $30 $31 emit emit ;", "10")


class BasicStackOperations(ChromaTest):
    """
    Some tests that the very basic stack operations are implemented correctly.
    Assumes a working "emit" operation.

    These operations are:
    dup, drop, swap, nip, over
    """

    def test_drop_emit(self):
        self.attempt("R main G $31 $30 drop emit ;", "1")

    def test_dup_lit_drop_emit(self):
        self.attempt("R main G $30 dup $31 drop emit ;", "0")

    def test_swap(self):
        self.attempt("R main G $31 $30 swap emit ;", "1")

    def test_nip(self):
        self.attempt("R main G $30 $31 $32 nip emit emit ;", "20")
        
    def test_over(self):
        self.attempt("R main G $39 $30 $31 over emit emit emit emit ;", "0109")

    def test_stack_depth(self):
        lits = " ".join(str(i) for i in range(0x20, 0x80))
        expect = "".join(chr(i) for i in range(0x7f, 0x1f, -1))
        self.attempt(f"R main G {lits} {'emit ' * (0x60)} ;", expect)


class BasicArithmeticOperations(ChromaTest):
    """
    Testing basic arithmetic operations. These are
    
    +, -, 1+, 1-, neg
    """

    def test_addition(self):
        self.attempt("R main G $30 $1 + emit ;", "1")
    
    def test_subtraction(self):
        self.attempt("R main G $32 1 - emit ;", "1")

    def test_increment(self):
        self.attempt("R main G $30 1+ emit ;", "1")

    def test_decrement(self):
        self.attempt("R main G $31 1- emit ;", "0")
        
    def test_neg(self):
        self.attempt("R main G 0 $31 - neg emit ;", "1")


class BasicLogicOperations(ChromaTest):
    """
    Test basic logic operations. These are:
    
    and, or, xor
    """
    
    def test_and(self):
        self.attempt("R main G $33 $31 and emit ;", "1")
        
    def test_or(self):
        self.attempt("R main G $30 $1 or emit ;", "1")
        
    def test_xor(self):
        self.attempt("R main G $b0 $81 xor emit ;", "1")


class ShiftRotationOperations(ChromaTest):
    """
    Tests for operations involving shifts. These include:
    
    shr, shl
    """
    
    def test_shr(self):
        self.attempt(f"R main G {ord('1') << 1} 1 shr emit ;", "1")
        
    def test_shl(self):
        self.attempt(f"R main G {ord('0') >> 1} 1 shl emit ;", "0")
        
    def test_rot(self):
        self.attempt("R main G $31 $32 $33 rot emit emit emit ;", "132")
    
    def test_nrot(self):
        self.attempt("R main G $31 $32 $33 -rot emit emit emit ;", "213")


class ReturnStackOperations(ChromaTest):
    """
    Tests for operations that manipulate the return stack:
    
    >r, r>, r@ 
    """
    
    def test_to_rstack(self):
        self.attempt("R main G $39 $30 >r emit r> ;", "9")
    
    def test_to_from_rstack(self):
        self.attempt("R main G $39 $30 $31 >r >r r> r> emit emit emit ;", "109")
        
    def test_rdup(self):
        self.attempt("R main G $39 $31 >r r@ emit r> ;", "1")


class MultiplicationDivisionOperations(ChromaTest):
    """
    Test multiplication and division opertaions. These include:
    
    *, /mod, /, mod
    """
    
    def test_mul(self):
        self.attempt("R main G 24 2 * emit ;", "0")

    def test_divmod(self):
        self.attempt("R main G 5 2 /mod $30 + emit $30 + emit ;", "21")

    def test_div(self):
        self.attempt("R main G 13 2 / $30 + emit ;", "6")

    def test_mod(self):
        self.attempt("R main G 11 10 mod $30 + emit ;", "1")


class ConditionalOperations(ChromaTest):
    """
    Testing basic conditionals:
    
    if, !if, -if, then
    """

    def test_if_should_drop(self):
        self.attempt("R main G $31 $30 if then emit ;", "1")

    def test_if_early_return(self):
        self.attempt("R main G $31 $30 if ; then emit ;", "")

    def test_if_should_skip(self):
        self.attempt("R main G $31 $0 if $30 then emit ;", "1")
    
    def test_nif_condition_true(self):
        self.attempt("R main G $0 !if $31 emit ; then ;", "1")
    
    def test_nif_condition_false(self):
        self.attempt("R main G $1 !if ; then $31 emit ;", "1")
    
    def test_nif_condition_skip(self):
        self.attempt("R main G $1 !if $30 emit ; then $31 emit ;", "1")
        
    def test_negative_if(self):
        self.attempt("R main G 0 1- -if $30 emit ; then $31 emit ;", "0")
        

class BranchingOperations(ChromaTest):
    """
    Test branches which aren't calls.
    """
    
    def test_back_jump(self):
        self.attempt("R done G $31 emit ; R main G $30 emit done ;", '01')
        
    def test_forward_jump(self):
        self.attempt("R main G done ; $30 emit R done G $31 emit ;", '1')
        

class SubroutineCallOperations(ChromaTest):
    """
    Test subroutine calls.
    """
    
    def test_back_call(self):
        self.attempt("R f G $31 emit ; R main G $30 emit f $32 emit ;", "012")
    
    def test_back_call(self):
        self.attempt("R main G $30 emit f $32 emit ; R f G $31 emit ;", "012")
        
    def test_jump_dest_also_a_jump_dest(self):
        self.attempt("R f G R main G ;", "")
        
    def test_recursion(self):
        factorial = "R f G dup !if drop 0 ; then dup 1- f + ; "
        self.attempt(factorial + "R main G 3 f $30 + emit ;", "6")
        

class IndirectSubroutineCallOperation(ChromaTest):
    """
    Test indirect subroutine call.
    
    go
    """
    
    def test_go(self):
        self.attempt('R dst G $31 emit ; R main G $32 emit Y dst G go $30 emit ;', '210')
        

class CountedLoopOperations(ChromaTest):
    """
    Test counted interation loops.
    
    for, next, ;;
    """
    
    #def test_for_zero_iterations(self):
    #    self.attempt("R main G $30 0 for dup emit 1+ next ;", "")
    
    def test_simple_for(self):
        self.attempt("R main G $30 5 for dup emit 1+ next ;", "01234")
        
    def test_loop_leave(self):
        self.attempt("R main G $30 5 for dup emit ;; next ;", "0")

    def test_conditional_in_loop(self):
        self.attempt("R main G $30 10 for dup 1 and !if dup emit then 1+ next ;", "02468")


class BasicMemoryOperations(ChromaTest):
    """
    Basic operations where memory is addressed using stack elements directly.
    These include:
    
    @, c@, ! 
    """
    
    def test_store(self):
        self.attempt("P mem R main G $30 mem ! ;", "")
    
    def test_fetch(self):
        self.attempt("P mem R main G mem @ ;", "")
    
    def test_fetch(self):
        self.attempt("P mem R main G $30 mem ! mem @ emit ;", "0")
    
    def test_store_fetch(self):
        self.attempt("P mem R main G $31 mem ! mem c@ emit ;", "1")
    

class ARegisterTests(ChromaTest):
    """
    Test operations involving the a register. These include:
    
    a, a!, !a, @a, +a, ++a, c!a, c@a
    """
    
    def test_simple_set_get(self):
        self.attempt("R main G $30 a! a emit ;", "0")

    def test_simple_increment(self):
        self.attempt("R main G $30 a! +a a emit ;", "1")

    def test_store_retrieve(self):
        self.attempt("R main P char G char a! $30 !a @a emit ;", "0")

    def test_store_increment_retrieve(self):
        self.attempt("R main P buf G buf a! +a $30 !a buf a! +a @a emit ;", "0")

    def test_increment_increment_word_retrieve(self):
        store = "buf a! $30 16 for dup !a ++a 1+ next "
        retrieve = "buf a! ++a @a "
        self.attempt("R main P buf G " + store + " " + retrieve + " emit ;", "1")
    
    def test_byte_store(self):
        self.attempt('R main P s G s a! $30 c!a ;', '')
       
    def test_byte_store_fetch(self):
        self.attempt('R main P s G s a! $30 c!a c@a emit ;', '0')

class StringTests(ChromaTest):
    """
    Test that string literals are stored as expected in data area.
    Requires c@ and a register working as expected.    
    """
    
    def test_correct_strlen_is_stored(self):
        self.attempt('R main G "hello" c@ $30 + emit ;', '5')
        
    def test_char_array_stored(self):
        self.attempt('R main G "hello" 1+ 5 for dup c@ emit 1+ next ;', 'hello')


class ImplementInternalCompilerWords(ChromaTest):
    """
    Ensure for the architecture words used by the compiler are implemented.
    
    word-size
    """
    
    def test_word_size(self):
        self.attempt('R main G word-size ;', '')
    
    
class SixteenBitLECompliance(ChromaTest):
    """
    Architectures should provide at least 16-bit arithmetic.
    Explore here certain edge cases -- particularly for 8-bit systems 
    non-natively implementing larger data widths.    
    """
    def test_16_bit_lit_low(self):
        self.attempt('R main G $3031 $ff and emit ;', '1')
    
    def test_16_bit_lit_hi(self):
        self.attempt('R main G $3130 8 shr $ff and emit ;', '1')
    
    def test_16_add_rollover(self):
        self.attempt('R main G $ff 1 + dup $30 + $ff and emit 8 shr $30 + $ff and emit ;', '01')
    
    
    
