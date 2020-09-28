import warnings
warnings.warn("Importing discussion.notification_prefs instead of lms.djangoapps.discussion.notification_prefs is deprecated", stacklevel=2)

from lms.djangoapps.discussion.notification_prefs import *
