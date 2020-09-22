import warnings
warnings.warn("Importing grades.tests instead of lms.djangoapps.grades.tests is deprecated", stacklevel=2)

from lms.djangoapps.grades.tests import *
