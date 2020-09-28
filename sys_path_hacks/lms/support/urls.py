import warnings
warnings.warn("Importing support.urls instead of lms.djangoapps.support.urls is deprecated", stacklevel=2)

from lms.djangoapps.support.urls import *
