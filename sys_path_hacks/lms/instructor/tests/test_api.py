import warnings
warnings.warn("Importing instructor.tests.test_api instead of lms.djangoapps.instructor.tests.test_api is deprecated", stacklevel=2)

from lms.djangoapps.instructor.tests.test_api import *
