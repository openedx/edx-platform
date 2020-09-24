import warnings
warnings.warn("Importing instructor.tests instead of lms.djangoapps.instructor.tests is deprecated", stacklevel=2)

from lms.djangoapps.instructor.tests import *
