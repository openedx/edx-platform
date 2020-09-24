import warnings
warnings.warn("Importing dashboard.management instead of lms.djangoapps.dashboard.management is deprecated", stacklevel=2)

from lms.djangoapps.dashboard.management import *
