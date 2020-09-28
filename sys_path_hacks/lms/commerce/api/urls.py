import warnings
warnings.warn("Importing commerce.api.urls instead of lms.djangoapps.commerce.api.urls is deprecated", stacklevel=2)

from lms.djangoapps.commerce.api.urls import *
