import warnings
warnings.warn("Importing certificates.admin instead of lms.djangoapps.certificates.admin is deprecated", stacklevel=2)

from lms.djangoapps.certificates.admin import *
