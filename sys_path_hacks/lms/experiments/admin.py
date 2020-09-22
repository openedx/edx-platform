import warnings
warnings.warn("Importing experiments.admin instead of lms.djangoapps.experiments.admin is deprecated", stacklevel=2)

from lms.djangoapps.experiments.admin import *
