import warnings
warnings.warn("Importing bulk_email instead of lms.djangoapps.bulk_email is deprecated", stacklevel=2)

from lms.djangoapps.bulk_email import *
