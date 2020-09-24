import warnings
warnings.warn("Importing dashboard.sysadmin instead of lms.djangoapps.dashboard.sysadmin is deprecated", stacklevel=2)

from lms.djangoapps.dashboard.sysadmin import *
