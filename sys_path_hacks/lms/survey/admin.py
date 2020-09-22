import warnings
warnings.warn("Importing survey.admin instead of lms.djangoapps.survey.admin is deprecated", stacklevel=2)

from lms.djangoapps.survey.admin import *
