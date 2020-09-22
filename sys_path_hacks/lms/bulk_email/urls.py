import warnings
warnings.warn("Importing bulk_email.urls instead of lms.djangoapps.bulk_email.urls is deprecated", stacklevel=2)

from lms.djangoapps.bulk_email.urls import *
