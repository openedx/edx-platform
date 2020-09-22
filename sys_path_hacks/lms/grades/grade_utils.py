import warnings
warnings.warn("Importing grades.grade_utils instead of lms.djangoapps.grades.grade_utils is deprecated", stacklevel=2)

from lms.djangoapps.grades.grade_utils import *
