import warnings
warnings.warn("Importing discussion.notifier_api instead of lms.djangoapps.discussion.notifier_api is deprecated", stacklevel=2)

from lms.djangoapps.discussion.notifier_api import *
