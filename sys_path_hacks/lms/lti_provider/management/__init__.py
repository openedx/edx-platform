import warnings
warnings.warn("Importing lti_provider.management instead of lms.djangoapps.lti_provider.management is deprecated", stacklevel=2)

from lms.djangoapps.lti_provider.management import *
