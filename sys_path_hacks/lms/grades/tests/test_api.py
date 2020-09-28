import warnings
warnings.warn("Importing grades.tests.test_api instead of lms.djangoapps.grades.tests.test_api is deprecated", stacklevel=2)

from lms.djangoapps.grades.tests.test_api import *
