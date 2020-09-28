import warnings
warnings.warn("Importing courseware.management.commands.dump_course_ids instead of lms.djangoapps.courseware.management.commands.dump_course_ids is deprecated", stacklevel=2)

from lms.djangoapps.courseware.management.commands.dump_course_ids import *
