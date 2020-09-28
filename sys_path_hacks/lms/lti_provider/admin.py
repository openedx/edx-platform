import warnings
warnings.warn("Importing lti_provider.admin instead of lms.djangoapps.lti_provider.admin is deprecated", stacklevel=2)

from lms.djangoapps.lti_provider.admin import *
