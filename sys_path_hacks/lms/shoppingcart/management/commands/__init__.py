import warnings
warnings.warn("Importing shoppingcart.management.commands instead of lms.djangoapps.shoppingcart.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.shoppingcart.management.commands import *
