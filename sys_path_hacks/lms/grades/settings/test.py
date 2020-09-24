import warnings
warnings.warn("Importing grades.settings.test instead of lms.djangoapps.grades.settings.test is deprecated", stacklevel=2)

from lms.djangoapps.grades.settings.test import *
