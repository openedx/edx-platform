import warnings
warnings.warn("Importing grades.models_api instead of lms.djangoapps.grades.models_api is deprecated", stacklevel=2)

from lms.djangoapps.grades.models_api import *
