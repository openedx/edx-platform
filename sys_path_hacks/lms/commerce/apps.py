import warnings
warnings.warn("Importing commerce.apps instead of lms.djangoapps.commerce.apps is deprecated", stacklevel=2)

from lms.djangoapps.commerce.apps import *
