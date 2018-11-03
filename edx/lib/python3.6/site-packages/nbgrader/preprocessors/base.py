from nbconvert.preprocessors import Preprocessor
from traitlets import List, Unicode, Bool

class NbGraderPreprocessor(Preprocessor):

    default_language = Unicode('ipython')
    display_data_priority = List(['text/html', 'application/pdf', 'text/latex', 'image/svg+xml', 'image/png', 'image/jpeg', 'text/plain'])
    enabled = Bool(True, help="Whether to use this preprocessor when running nbgrader").tag(config=True)
