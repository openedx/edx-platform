import warnings
warnings.warn("Importing survey.signals instead of lms.djangoapps.survey.signals is deprecated", stacklevel=2)

from lms.djangoapps.survey.signals import *
