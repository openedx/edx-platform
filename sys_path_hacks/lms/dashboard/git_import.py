import warnings
warnings.warn("Importing dashboard.git_import instead of lms.djangoapps.dashboard.git_import is deprecated", stacklevel=2)

from lms.djangoapps.dashboard.git_import import *
