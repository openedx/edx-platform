import warnings
warnings.warn("Importing instructor.settings.devstack instead of lms.djangoapps.instructor.settings.devstack is deprecated", stacklevel=2)

from lms.djangoapps.instructor.settings.devstack import *
