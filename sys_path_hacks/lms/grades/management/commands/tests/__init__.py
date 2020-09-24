import warnings
warnings.warn("Importing grades.management.commands.tests instead of lms.djangoapps.grades.management.commands.tests is deprecated", stacklevel=2)

from lms.djangoapps.grades.management.commands.tests import *
