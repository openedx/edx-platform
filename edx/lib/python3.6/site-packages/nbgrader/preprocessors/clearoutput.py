from nbconvert.preprocessors import ClearOutputPreprocessor
from . import NbGraderPreprocessor

class ClearOutput(NbGraderPreprocessor, ClearOutputPreprocessor):
    pass