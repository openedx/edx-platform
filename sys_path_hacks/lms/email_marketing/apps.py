import warnings
warnings.warn("Importing email_marketing.apps instead of lms.djangoapps.email_marketing.apps is deprecated", stacklevel=2)

from lms.djangoapps.email_marketing.apps import *
