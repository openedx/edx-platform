import warnings
warnings.warn("Importing lti_provider.tasks instead of lms.djangoapps.lti_provider.tasks is deprecated", stacklevel=2)

from lms.djangoapps.lti_provider.tasks import *
