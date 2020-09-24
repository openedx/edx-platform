import warnings
warnings.warn("Importing certificates.apps instead of lms.djangoapps.certificates.apps is deprecated", stacklevel=2)

from lms.djangoapps.certificates.apps import *
