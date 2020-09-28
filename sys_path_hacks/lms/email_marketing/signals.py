import warnings
warnings.warn("Importing email_marketing.signals instead of lms.djangoapps.email_marketing.signals is deprecated", stacklevel=2)

from lms.djangoapps.email_marketing.signals import *
