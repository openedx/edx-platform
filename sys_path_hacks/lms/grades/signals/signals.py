import warnings
warnings.warn("Importing grades.signals.signals instead of lms.djangoapps.grades.signals.signals is deprecated", stacklevel=2)

from lms.djangoapps.grades.signals.signals import *
