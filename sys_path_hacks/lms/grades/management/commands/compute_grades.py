import warnings
warnings.warn("Importing grades.management.commands.compute_grades instead of lms.djangoapps.grades.management.commands.compute_grades is deprecated", stacklevel=2)

from lms.djangoapps.grades.management.commands.compute_grades import *
