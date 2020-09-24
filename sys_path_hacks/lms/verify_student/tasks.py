import warnings
warnings.warn("Importing verify_student.tasks instead of lms.djangoapps.verify_student.tasks is deprecated", stacklevel=2)

from lms.djangoapps.verify_student.tasks import *
