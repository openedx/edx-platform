import warnings
warnings.warn("Importing lti_provider instead of lms.djangoapps.lti_provider is deprecated", stacklevel=2)

from lms.djangoapps.lti_provider import *
