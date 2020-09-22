import warnings
warnings.warn("Importing lti_provider.management.commands instead of lms.djangoapps.lti_provider.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.lti_provider.management.commands import *
