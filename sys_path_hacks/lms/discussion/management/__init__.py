import warnings
warnings.warn("Importing discussion.management instead of lms.djangoapps.discussion.management is deprecated", stacklevel=2)

from lms.djangoapps.discussion.management import *
