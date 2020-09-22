import warnings
warnings.warn("Importing email_marketing instead of lms.djangoapps.email_marketing is deprecated", stacklevel=2)

from lms.djangoapps.email_marketing import *
