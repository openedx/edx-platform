import warnings
warnings.warn("Importing branding.admin instead of lms.djangoapps.branding.admin is deprecated", stacklevel=2)

from lms.djangoapps.branding.admin import *
