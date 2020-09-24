import warnings
warnings.warn("Importing email_marketing.tasks instead of lms.djangoapps.email_marketing.tasks is deprecated", stacklevel=2)

from lms.djangoapps.email_marketing.tasks import *
