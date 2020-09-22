import warnings
warnings.warn("Importing survey.apps instead of lms.djangoapps.survey.apps is deprecated", stacklevel=2)

from lms.djangoapps.survey.apps import *
