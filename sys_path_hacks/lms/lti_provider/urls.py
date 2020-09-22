import warnings
warnings.warn("Importing lti_provider.urls instead of lms.djangoapps.lti_provider.urls is deprecated", stacklevel=2)

from lms.djangoapps.lti_provider.urls import *
