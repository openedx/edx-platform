import warnings
warnings.warn("Importing experiments.serializers instead of lms.djangoapps.experiments.serializers is deprecated", stacklevel=2)

from lms.djangoapps.experiments.serializers import *
