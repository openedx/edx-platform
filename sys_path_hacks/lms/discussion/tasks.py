import warnings
warnings.warn("Importing discussion.tasks instead of lms.djangoapps.discussion.tasks is deprecated", stacklevel=2)

from lms.djangoapps.discussion.tasks import *
