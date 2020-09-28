import warnings
warnings.warn("Importing support.views.manage_user instead of lms.djangoapps.support.views.manage_user is deprecated", stacklevel=2)

from lms.djangoapps.support.views.manage_user import *
