import warnings
warnings.warn("Importing survey.tests instead of lms.djangoapps.survey.tests is deprecated", stacklevel=2)

from lms.djangoapps.survey.tests import *
