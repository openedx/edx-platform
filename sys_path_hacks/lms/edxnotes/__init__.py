import warnings
warnings.warn("Importing edxnotes instead of lms.djangoapps.edxnotes is deprecated", stacklevel=2)

from lms.djangoapps.edxnotes import *
