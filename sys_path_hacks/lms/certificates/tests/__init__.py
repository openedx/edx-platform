import warnings
warnings.warn("Importing certificates.tests instead of lms.djangoapps.certificates.tests is deprecated", stacklevel=2)

from lms.djangoapps.certificates.tests import *
