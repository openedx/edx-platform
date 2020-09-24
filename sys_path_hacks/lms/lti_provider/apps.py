import warnings
warnings.warn("Importing lti_provider.apps instead of lms.djangoapps.lti_provider.apps is deprecated", stacklevel=2)

from lms.djangoapps.lti_provider.apps import *
