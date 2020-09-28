import warnings
warnings.warn("Importing branding.api instead of lms.djangoapps.branding.api is deprecated", stacklevel=2)

from lms.djangoapps.branding.api import *
