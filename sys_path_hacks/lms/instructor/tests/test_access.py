import warnings
warnings.warn("Importing instructor.tests.test_access instead of lms.djangoapps.instructor.tests.test_access is deprecated", stacklevel=2)

from lms.djangoapps.instructor.tests.test_access import *
