import warnings
warnings.warn("Importing experiments.routers instead of lms.djangoapps.experiments.routers is deprecated", stacklevel=2)

from lms.djangoapps.experiments.routers import *
