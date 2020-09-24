import warnings
warnings.warn("Importing instructor.settings.test instead of lms.djangoapps.instructor.settings.test is deprecated", stacklevel=2)

from lms.djangoapps.instructor.settings.test import *
