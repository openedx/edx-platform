import warnings
warnings.warn("Importing certificates.urls instead of lms.djangoapps.certificates.urls is deprecated", stacklevel=2)

from lms.djangoapps.certificates.urls import *
