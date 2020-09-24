import warnings
warnings.warn("Importing courseware.tests instead of lms.djangoapps.courseware.tests is deprecated", stacklevel=2)

from lms.djangoapps.courseware.tests import *
