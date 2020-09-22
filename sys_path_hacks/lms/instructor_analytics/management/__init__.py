import warnings
warnings.warn("Importing instructor_analytics.management instead of lms.djangoapps.instructor_analytics.management is deprecated", stacklevel=2)

from lms.djangoapps.instructor_analytics.management import *
