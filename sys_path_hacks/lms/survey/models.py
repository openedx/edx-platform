import warnings
warnings.warn("Importing survey.models instead of lms.djangoapps.survey.models is deprecated", stacklevel=2)

from lms.djangoapps.survey.models import *
