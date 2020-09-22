import warnings
warnings.warn("Importing bulk_enroll instead of lms.djangoapps.bulk_enroll is deprecated", stacklevel=2)

from lms.djangoapps.bulk_enroll import *
