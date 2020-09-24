import warnings
warnings.warn("Importing certificates.services instead of lms.djangoapps.certificates.services is deprecated", stacklevel=2)

from lms.djangoapps.certificates.services import *
