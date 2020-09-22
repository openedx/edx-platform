import warnings
warnings.warn("Importing lti_provider.signature_validator instead of lms.djangoapps.lti_provider.signature_validator is deprecated", stacklevel=2)

from lms.djangoapps.lti_provider.signature_validator import *
