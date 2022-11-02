from .test_common import *

class CompleteTestSuite(
    SimpleEmit,
    BasicStackOperations, 
    BasicArithmeticOperations,
    BasicLogicOperations,
    ShiftRotationOperations,
    ReturnStackOperations,
    MultiplicationDivisionOperations,
    ConditionalOperations,
    BranchingOperations,
    SubroutineCallOperations,
    CountedLoopOperations,
    BasicMemoryOperations,
    ARegisterTests,
    StringTests,
):
    """
    Test suite for a system implementing all words.
    """
    pass