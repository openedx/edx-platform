import warnings
warnings.warn("Importing instructor.message_types instead of lms.djangoapps.instructor.message_types is deprecated", stacklevel=2)

from lms.djangoapps.instructor.message_types import *
