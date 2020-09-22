import warnings
warnings.warn("Importing grades.rest_api instead of lms.djangoapps.grades.rest_api is deprecated", stacklevel=2)

from lms.djangoapps.grades.rest_api import *
