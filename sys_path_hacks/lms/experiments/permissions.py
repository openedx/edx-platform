import warnings
warnings.warn("Importing experiments.permissions instead of lms.djangoapps.experiments.permissions is deprecated", stacklevel=2)

from lms.djangoapps.experiments.permissions import *
