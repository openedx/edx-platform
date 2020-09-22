import warnings
warnings.warn("Importing gating.signals instead of lms.djangoapps.gating.signals is deprecated", stacklevel=2)

from lms.djangoapps.gating.signals import *
