import warnings
warnings.warn("Importing edxnotes.plugins instead of lms.djangoapps.edxnotes.plugins is deprecated", stacklevel=2)

from lms.djangoapps.edxnotes.plugins import *
