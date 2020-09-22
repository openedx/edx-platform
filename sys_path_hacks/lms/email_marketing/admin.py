import warnings
warnings.warn("Importing email_marketing.admin instead of lms.djangoapps.email_marketing.admin is deprecated", stacklevel=2)

from lms.djangoapps.email_marketing.admin import *
