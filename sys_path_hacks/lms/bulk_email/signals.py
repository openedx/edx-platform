import warnings
warnings.warn("Importing bulk_email.signals instead of lms.djangoapps.bulk_email.signals is deprecated", stacklevel=2)

from lms.djangoapps.bulk_email.signals import *
