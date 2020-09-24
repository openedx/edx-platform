import warnings
warnings.warn("Importing courseware.management.commands.tests instead of lms.djangoapps.courseware.management.commands.tests is deprecated", stacklevel=2)

from lms.djangoapps.courseware.management.commands.tests import *
