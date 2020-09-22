import warnings
warnings.warn("Importing grades.scores instead of lms.djangoapps.grades.scores is deprecated", stacklevel=2)

from lms.djangoapps.grades.scores import *
