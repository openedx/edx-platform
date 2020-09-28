import warnings
warnings.warn("Importing grades.settings.common instead of lms.djangoapps.grades.settings.common is deprecated", stacklevel=2)

from lms.djangoapps.grades.settings.common import *
