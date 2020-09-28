import warnings
warnings.warn("Importing commerce.management.commands instead of lms.djangoapps.commerce.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.commerce.management.commands import *
