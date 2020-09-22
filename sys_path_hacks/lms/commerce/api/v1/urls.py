import warnings
warnings.warn("Importing commerce.api.v1.urls instead of lms.djangoapps.commerce.api.v1.urls is deprecated", stacklevel=2)

from lms.djangoapps.commerce.api.v1.urls import *
