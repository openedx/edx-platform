import warnings
warnings.warn("Importing bulk_email.admin instead of lms.djangoapps.bulk_email.admin is deprecated", stacklevel=2)

from lms.djangoapps.bulk_email.admin import *
