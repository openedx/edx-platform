import warnings
warnings.warn("Importing grades.tasks instead of lms.djangoapps.grades.tasks is deprecated", stacklevel=2)

from lms.djangoapps.grades.tasks import *
