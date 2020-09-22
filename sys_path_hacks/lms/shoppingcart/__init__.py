import warnings
warnings.warn("Importing shoppingcart instead of lms.djangoapps.shoppingcart is deprecated", stacklevel=2)

from lms.djangoapps.shoppingcart import *
