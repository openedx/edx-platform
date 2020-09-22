import warnings
warnings.warn("Importing discussion.apps instead of lms.djangoapps.discussion.apps is deprecated", stacklevel=2)

from lms.djangoapps.discussion.apps import *
