import warnings
warnings.warn("Importing shoppingcart.management instead of lms.djangoapps.shoppingcart.management is deprecated", stacklevel=2)

from lms.djangoapps.shoppingcart.management import *
