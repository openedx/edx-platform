import warnings
warnings.warn("Importing course_api.serializers instead of lms.djangoapps.course_api.serializers is deprecated", stacklevel=2)

from lms.djangoapps.course_api.serializers import *
