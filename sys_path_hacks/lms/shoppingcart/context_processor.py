import warnings
warnings.warn("Importing shoppingcart.context_processor instead of lms.djangoapps.shoppingcart.context_processor is deprecated", stacklevel=2)

from lms.djangoapps.shoppingcart.context_processor import *
