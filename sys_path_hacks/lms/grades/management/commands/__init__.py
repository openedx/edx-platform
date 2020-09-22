import warnings
warnings.warn("Importing grades.management.commands instead of lms.djangoapps.grades.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.grades.management.commands import *
