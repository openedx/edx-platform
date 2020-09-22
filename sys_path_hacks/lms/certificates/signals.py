import warnings
warnings.warn("Importing certificates.signals instead of lms.djangoapps.certificates.signals is deprecated", stacklevel=2)

from lms.djangoapps.certificates.signals import *
