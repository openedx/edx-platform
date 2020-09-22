import warnings
warnings.warn("Importing courseware.tests.tests instead of lms.djangoapps.courseware.tests.tests is deprecated", stacklevel=2)

from lms.djangoapps.courseware.tests.tests import *
