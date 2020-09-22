import warnings
warnings.warn("Importing gating.apps instead of lms.djangoapps.gating.apps is deprecated", stacklevel=2)

from lms.djangoapps.gating.apps import *
