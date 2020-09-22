import warnings
warnings.warn("Importing commerce.api.v0.urls instead of lms.djangoapps.commerce.api.v0.urls is deprecated", stacklevel=2)

from lms.djangoapps.commerce.api.v0.urls import *
