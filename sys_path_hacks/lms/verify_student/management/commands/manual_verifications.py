import warnings
warnings.warn("Importing verify_student.management.commands.manual_verifications instead of lms.djangoapps.verify_student.management.commands.manual_verifications is deprecated", stacklevel=2)

from lms.djangoapps.verify_student.management.commands.manual_verifications import *
