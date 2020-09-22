import warnings
warnings.warn("Importing experiments.apps instead of lms.djangoapps.experiments.apps is deprecated", stacklevel=2)

from lms.djangoapps.experiments.apps import *
