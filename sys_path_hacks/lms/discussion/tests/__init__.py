import warnings
warnings.warn("Importing discussion.tests instead of lms.djangoapps.discussion.tests is deprecated", stacklevel=2)

from lms.djangoapps.discussion.tests import *
