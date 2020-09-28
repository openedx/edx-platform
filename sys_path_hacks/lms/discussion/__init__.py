import warnings
warnings.warn("Importing discussion instead of lms.djangoapps.discussion is deprecated", stacklevel=2)

from lms.djangoapps.discussion import *
