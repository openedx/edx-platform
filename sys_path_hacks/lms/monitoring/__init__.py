import warnings
warnings.warn("Importing monitoring instead of lms.djangoapps.monitoring is deprecated", stacklevel=2)

from lms.djangoapps.monitoring import *
