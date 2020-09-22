import warnings
warnings.warn("Importing grades.tests.test_tasks instead of lms.djangoapps.grades.tests.test_tasks is deprecated", stacklevel=2)

from lms.djangoapps.grades.tests.test_tasks import *
