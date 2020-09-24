import warnings
warnings.warn("Importing certificates.tests.test_queue instead of lms.djangoapps.certificates.tests.test_queue is deprecated", stacklevel=2)

from lms.djangoapps.certificates.tests.test_queue import *
