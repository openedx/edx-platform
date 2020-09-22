import warnings
warnings.warn("Importing badges.events.course_complete instead of lms.djangoapps.badges.events.course_complete is deprecated", stacklevel=2)

from lms.djangoapps.badges.events.course_complete import *
