import warnings
warnings.warn("Importing lms_xblock.models instead of lms.djangoapps.lms_xblock.models is deprecated", stacklevel=2)

from lms.djangoapps.lms_xblock.models import *
