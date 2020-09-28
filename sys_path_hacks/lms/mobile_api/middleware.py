import warnings
warnings.warn("Importing mobile_api.middleware instead of lms.djangoapps.mobile_api.middleware is deprecated", stacklevel=2)

from lms.djangoapps.mobile_api.middleware import *
