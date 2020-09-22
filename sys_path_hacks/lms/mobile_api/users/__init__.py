import warnings
warnings.warn("Importing mobile_api.users instead of lms.djangoapps.mobile_api.users is deprecated", stacklevel=2)

from lms.djangoapps.mobile_api.users import *
