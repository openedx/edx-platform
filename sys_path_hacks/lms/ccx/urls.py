import warnings
warnings.warn("Importing ccx.urls instead of lms.djangoapps.ccx.urls is deprecated", stacklevel=2)

from lms.djangoapps.ccx.urls import *
