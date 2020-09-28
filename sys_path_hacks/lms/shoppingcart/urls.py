import warnings
warnings.warn("Importing shoppingcart.urls instead of lms.djangoapps.shoppingcart.urls is deprecated", stacklevel=2)

from lms.djangoapps.shoppingcart.urls import *
