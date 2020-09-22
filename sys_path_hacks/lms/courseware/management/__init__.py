import warnings
warnings.warn("Importing courseware.management instead of lms.djangoapps.courseware.management is deprecated", stacklevel=2)

from lms.djangoapps.courseware.management import *
