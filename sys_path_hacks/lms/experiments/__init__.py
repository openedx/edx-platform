import warnings
warnings.warn("Importing experiments instead of lms.djangoapps.experiments is deprecated", stacklevel=2)

from lms.djangoapps.experiments import *
