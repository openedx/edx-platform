import warnings
warnings.warn("Importing grades.apps instead of lms.djangoapps.grades.apps is deprecated", stacklevel=2)

from lms.djangoapps.grades.apps import *
