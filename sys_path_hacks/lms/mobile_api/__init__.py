import warnings
warnings.warn("Importing mobile_api instead of lms.djangoapps.mobile_api is deprecated", stacklevel=2)

from lms.djangoapps.mobile_api import *
