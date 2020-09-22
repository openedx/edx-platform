import warnings
warnings.warn("Importing instructor_analytics.csvs instead of lms.djangoapps.instructor_analytics.csvs is deprecated", stacklevel=2)

from lms.djangoapps.instructor_analytics.csvs import *
