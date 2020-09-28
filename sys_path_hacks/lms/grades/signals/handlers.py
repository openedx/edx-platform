import warnings
warnings.warn("Importing grades.signals.handlers instead of lms.djangoapps.grades.signals.handlers is deprecated", stacklevel=2)

from lms.djangoapps.grades.signals.handlers import *
