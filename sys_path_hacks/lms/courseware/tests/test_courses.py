import warnings
warnings.warn("Importing courseware.tests.test_courses instead of lms.djangoapps.courseware.tests.test_courses is deprecated", stacklevel=2)

from lms.djangoapps.courseware.tests.test_courses import *
