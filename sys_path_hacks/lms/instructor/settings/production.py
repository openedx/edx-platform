import warnings
warnings.warn("Importing instructor.settings.production instead of lms.djangoapps.instructor.settings.production is deprecated", stacklevel=2)

from lms.djangoapps.instructor.settings.production import *
