import warnings
warnings.warn("Importing dashboard.sysadmin_urls instead of lms.djangoapps.dashboard.sysadmin_urls is deprecated", stacklevel=2)

from lms.djangoapps.dashboard.sysadmin_urls import *
