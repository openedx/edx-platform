import warnings
warnings.warn("Importing tests instead of lms.djangoapps.tests is deprecated", stacklevel=2)

from lms.djangoapps.tests import *
