import warnings
warnings.warn("Importing discussion.signals.handlers instead of lms.djangoapps.discussion.signals.handlers is deprecated", stacklevel=2)

from lms.djangoapps.discussion.signals.handlers import *
