import warnings
warnings.warn("Importing grades.management instead of lms.djangoapps.grades.management is deprecated", stacklevel=2)

from lms.djangoapps.grades.management import *
