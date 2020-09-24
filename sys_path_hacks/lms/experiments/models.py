import warnings
warnings.warn("Importing experiments.models instead of lms.djangoapps.experiments.models is deprecated", stacklevel=2)

from lms.djangoapps.experiments.models import *
