import warnings
warnings.warn("Importing commerce.tests instead of lms.djangoapps.commerce.tests is deprecated", stacklevel=2)

from lms.djangoapps.commerce.tests import *
