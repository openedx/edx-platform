import warnings
warnings.warn("Importing dashboard.tests instead of lms.djangoapps.dashboard.tests is deprecated", stacklevel=2)

from lms.djangoapps.dashboard.tests import *
