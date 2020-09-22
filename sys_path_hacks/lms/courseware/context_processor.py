import warnings
warnings.warn("Importing courseware.context_processor instead of lms.djangoapps.courseware.context_processor is deprecated", stacklevel=2)

from lms.djangoapps.courseware.context_processor import *
