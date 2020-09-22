import warnings
warnings.warn("Importing mobile_api.context_processor instead of lms.djangoapps.mobile_api.context_processor is deprecated", stacklevel=2)

from lms.djangoapps.mobile_api.context_processor import *
