import warnings
warnings.warn("Importing debug.management.commands instead of lms.djangoapps.debug.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.debug.management.commands import *
