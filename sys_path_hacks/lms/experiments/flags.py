import warnings
warnings.warn("Importing experiments.flags instead of lms.djangoapps.experiments.flags is deprecated", stacklevel=2)

from lms.djangoapps.experiments.flags import *
