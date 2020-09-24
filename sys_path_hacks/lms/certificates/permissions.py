import warnings
warnings.warn("Importing certificates.permissions instead of lms.djangoapps.certificates.permissions is deprecated", stacklevel=2)

from lms.djangoapps.certificates.permissions import *
