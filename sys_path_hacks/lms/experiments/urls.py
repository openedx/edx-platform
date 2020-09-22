import warnings
warnings.warn("Importing experiments.urls instead of lms.djangoapps.experiments.urls is deprecated", stacklevel=2)

from lms.djangoapps.experiments.urls import *
