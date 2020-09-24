import warnings
warnings.warn("Importing certificates.queue instead of lms.djangoapps.certificates.queue is deprecated", stacklevel=2)

from lms.djangoapps.certificates.queue import *
