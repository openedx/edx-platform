import warnings
warnings.warn("Importing ccx.tasks instead of lms.djangoapps.ccx.tasks is deprecated", stacklevel=2)

from lms.djangoapps.ccx.tasks import *
