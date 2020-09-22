import warnings
warnings.warn("Importing bulk_email.api instead of lms.djangoapps.bulk_email.api is deprecated", stacklevel=2)

from lms.djangoapps.bulk_email.api import *
