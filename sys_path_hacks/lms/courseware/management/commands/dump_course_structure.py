import warnings
warnings.warn("Importing courseware.management.commands.dump_course_structure instead of lms.djangoapps.courseware.management.commands.dump_course_structure is deprecated", stacklevel=2)

from lms.djangoapps.courseware.management.commands.dump_course_structure import *
