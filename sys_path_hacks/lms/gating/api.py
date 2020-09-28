import warnings
warnings.warn("Importing gating.api instead of lms.djangoapps.gating.api is deprecated", stacklevel=2)

from lms.djangoapps.gating.api import *
