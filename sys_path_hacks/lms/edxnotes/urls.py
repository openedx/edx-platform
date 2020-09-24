import warnings
warnings.warn("Importing edxnotes.urls instead of lms.djangoapps.edxnotes.urls is deprecated", stacklevel=2)

from lms.djangoapps.edxnotes.urls import *
