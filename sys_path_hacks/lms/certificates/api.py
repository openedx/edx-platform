import warnings
warnings.warn("Importing certificates.api instead of lms.djangoapps.certificates.api is deprecated", stacklevel=2)

from lms.djangoapps.certificates.api import *
