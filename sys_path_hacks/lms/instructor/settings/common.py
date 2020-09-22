import warnings
warnings.warn("Importing instructor.settings.common instead of lms.djangoapps.instructor.settings.common is deprecated", stacklevel=2)

from lms.djangoapps.instructor.settings.common import *
