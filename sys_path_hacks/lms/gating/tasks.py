import warnings
warnings.warn("Importing gating.tasks instead of lms.djangoapps.gating.tasks is deprecated", stacklevel=2)

from lms.djangoapps.gating.tasks import *
