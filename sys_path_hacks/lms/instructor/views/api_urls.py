import warnings
warnings.warn("Importing instructor.views.api_urls instead of lms.djangoapps.instructor.views.api_urls is deprecated", stacklevel=2)

from lms.djangoapps.instructor.views.api_urls import *
