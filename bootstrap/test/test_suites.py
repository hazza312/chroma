from .test_common import *

class BaseTestSuite(
    SimpleEmit,
    BasicStackOperations, 
    BasicArithmeticOperations,
    BasicLogicOperations,
    ShiftRotationOperations,
    ReturnStackOperations,
    ConditionalOperations,
    BranchingOperations,
    SubroutineCallOperations,
    CountedLoopOperations,
    BasicMemoryOperations,
    ARegisterTests,
    ImplementInternalCompilerWords
):
    """Test suite implementing base words"""
    pass
    
class CompleteTestSuite(
    BaseTestSuite,
    MultiplicationDivisionOperations,
    StringTests
):
    """
    Test suite for a system implementing all words.
    """
    pass