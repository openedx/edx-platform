import warnings
warnings.warn("Importing instructor.tests.test_enrollment instead of lms.djangoapps.instructor.tests.test_enrollment is deprecated", stacklevel=2)

from lms.djangoapps.instructor.tests.test_enrollment import *
