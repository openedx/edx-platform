import warnings
warnings.warn("Importing instructor_analytics.management.commands instead of lms.djangoapps.instructor_analytics.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.instructor_analytics.management.commands import *
