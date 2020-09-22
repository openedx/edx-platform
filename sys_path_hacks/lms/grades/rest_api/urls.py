import warnings
warnings.warn("Importing grades.rest_api.urls instead of lms.djangoapps.grades.rest_api.urls is deprecated", stacklevel=2)

from lms.djangoapps.grades.rest_api.urls import *
