import warnings
warnings.warn("Importing gating instead of lms.djangoapps.gating is deprecated", stacklevel=2)

from lms.djangoapps.gating import *
