import warnings
warnings.warn("Importing experiments.views_custom instead of lms.djangoapps.experiments.views_custom is deprecated", stacklevel=2)

from lms.djangoapps.experiments.views_custom import *
