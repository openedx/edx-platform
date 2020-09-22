import warnings
warnings.warn("Importing staticbook instead of lms.djangoapps.staticbook is deprecated", stacklevel=2)

from lms.djangoapps.staticbook import *
