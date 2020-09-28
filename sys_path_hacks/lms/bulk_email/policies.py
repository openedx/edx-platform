import warnings
warnings.warn("Importing bulk_email.policies instead of lms.djangoapps.bulk_email.policies is deprecated", stacklevel=2)

from lms.djangoapps.bulk_email.policies import *
