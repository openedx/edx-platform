import warnings
warnings.warn("Importing shoppingcart.admin instead of lms.djangoapps.shoppingcart.admin is deprecated", stacklevel=2)

from lms.djangoapps.shoppingcart.admin import *
