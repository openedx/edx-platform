import warnings
warnings.warn("Importing grades.settings.production instead of lms.djangoapps.grades.settings.production is deprecated", stacklevel=2)

from lms.djangoapps.grades.settings.production import *
