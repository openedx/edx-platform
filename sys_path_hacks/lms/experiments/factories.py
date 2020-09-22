import warnings
warnings.warn("Importing experiments.factories instead of lms.djangoapps.experiments.factories is deprecated", stacklevel=2)

from lms.djangoapps.experiments.factories import *
