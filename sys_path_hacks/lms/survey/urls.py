import warnings
warnings.warn("Importing survey.urls instead of lms.djangoapps.survey.urls is deprecated", stacklevel=2)

from lms.djangoapps.survey.urls import *
