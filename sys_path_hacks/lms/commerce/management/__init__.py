import warnings
warnings.warn("Importing commerce.management instead of lms.djangoapps.commerce.management is deprecated", stacklevel=2)

from lms.djangoapps.commerce.management import *
