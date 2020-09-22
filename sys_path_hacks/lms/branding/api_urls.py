import warnings
warnings.warn("Importing branding.api_urls instead of lms.djangoapps.branding.api_urls is deprecated", stacklevel=2)

from lms.djangoapps.branding.api_urls import *
