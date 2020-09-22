import warnings
warnings.warn("Importing certificates.tasks instead of lms.djangoapps.certificates.tasks is deprecated", stacklevel=2)

from lms.djangoapps.certificates.tasks import *
