import warnings
warnings.warn("Importing shoppingcart.api instead of lms.djangoapps.shoppingcart.api is deprecated", stacklevel=2)

from lms.djangoapps.shoppingcart.api import *
