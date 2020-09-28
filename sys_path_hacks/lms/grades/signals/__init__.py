import warnings
warnings.warn("Importing grades.signals instead of lms.djangoapps.grades.signals is deprecated", stacklevel=2)

from lms.djangoapps.grades.signals import *
