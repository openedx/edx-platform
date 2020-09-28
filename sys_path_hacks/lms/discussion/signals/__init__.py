import warnings
warnings.warn("Importing discussion.signals instead of lms.djangoapps.discussion.signals is deprecated", stacklevel=2)

from lms.djangoapps.discussion.signals import *
