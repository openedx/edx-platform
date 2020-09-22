import warnings
warnings.warn("Importing experiments.tests instead of lms.djangoapps.experiments.tests is deprecated", stacklevel=2)

from lms.djangoapps.experiments.tests import *
