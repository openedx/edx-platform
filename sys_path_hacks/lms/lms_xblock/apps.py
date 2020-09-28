import warnings
warnings.warn("Importing lms_xblock.apps instead of lms.djangoapps.lms_xblock.apps is deprecated", stacklevel=2)

from lms.djangoapps.lms_xblock.apps import *
