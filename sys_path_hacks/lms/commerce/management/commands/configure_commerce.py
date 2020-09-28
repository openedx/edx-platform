import warnings
warnings.warn("Importing commerce.management.commands.configure_commerce instead of lms.djangoapps.commerce.management.commands.configure_commerce is deprecated", stacklevel=2)

from lms.djangoapps.commerce.management.commands.configure_commerce import *
