import warnings
warnings.warn("Importing survey instead of lms.djangoapps.survey is deprecated", stacklevel=2)

from lms.djangoapps.survey import *
