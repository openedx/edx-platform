import warnings
warnings.warn("Importing dashboard.models instead of lms.djangoapps.dashboard.models is deprecated", stacklevel=2)

from lms.djangoapps.dashboard.models import *
