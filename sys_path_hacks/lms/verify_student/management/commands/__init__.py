import warnings
warnings.warn("Importing verify_student.management.commands instead of lms.djangoapps.verify_student.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.verify_student.management.commands import *
