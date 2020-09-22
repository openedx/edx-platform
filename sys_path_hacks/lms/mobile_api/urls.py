import warnings
warnings.warn("Importing mobile_api.urls instead of lms.djangoapps.mobile_api.urls is deprecated", stacklevel=2)

from lms.djangoapps.mobile_api.urls import *
