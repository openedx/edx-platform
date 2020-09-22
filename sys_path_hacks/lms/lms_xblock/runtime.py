import warnings
warnings.warn("Importing lms_xblock.runtime instead of lms.djangoapps.lms_xblock.runtime is deprecated", stacklevel=2)

from lms.djangoapps.lms_xblock.runtime import *
