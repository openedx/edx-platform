import warnings
warnings.warn("Importing lti_provider.users instead of lms.djangoapps.lti_provider.users is deprecated", stacklevel=2)

from lms.djangoapps.lti_provider.users import *
