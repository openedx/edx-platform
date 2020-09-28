import warnings
warnings.warn("Importing grades.tests.test_scores instead of lms.djangoapps.grades.tests.test_scores is deprecated", stacklevel=2)

from lms.djangoapps.grades.tests.test_scores import *
