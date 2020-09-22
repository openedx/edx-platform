import warnings
warnings.warn("Importing grades.transformer instead of lms.djangoapps.grades.transformer is deprecated", stacklevel=2)

from lms.djangoapps.grades.transformer import *
