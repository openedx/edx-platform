import warnings
warnings.warn("Importing grades.tests.base instead of lms.djangoapps.grades.tests.base is deprecated", stacklevel=2)

from lms.djangoapps.grades.tests.base import *
