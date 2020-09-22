import warnings
warnings.warn("Importing experiments.stable_bucketing instead of lms.djangoapps.experiments.stable_bucketing is deprecated", stacklevel=2)

from lms.djangoapps.experiments.stable_bucketing import *
