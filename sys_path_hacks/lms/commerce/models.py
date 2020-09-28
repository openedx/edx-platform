import warnings
warnings.warn("Importing commerce.models instead of lms.djangoapps.commerce.models is deprecated", stacklevel=2)

from lms.djangoapps.commerce.models import *
