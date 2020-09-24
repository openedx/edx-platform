import warnings
warnings.warn("Importing lti_provider.signals instead of lms.djangoapps.lti_provider.signals is deprecated", stacklevel=2)

from lms.djangoapps.lti_provider.signals import *
