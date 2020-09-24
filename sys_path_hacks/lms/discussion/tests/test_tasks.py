import warnings
warnings.warn("Importing discussion.tests.test_tasks instead of lms.djangoapps.discussion.tests.test_tasks is deprecated", stacklevel=2)

from lms.djangoapps.discussion.tests.test_tasks import *
