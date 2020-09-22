import warnings
warnings.warn("Importing courseware.model_data instead of lms.djangoapps.courseware.model_data is deprecated", stacklevel=2)

from lms.djangoapps.courseware.model_data import *
