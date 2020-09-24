import warnings
warnings.warn("Importing edxnotes.api_urls instead of lms.djangoapps.edxnotes.api_urls is deprecated", stacklevel=2)

from lms.djangoapps.edxnotes.api_urls import *
