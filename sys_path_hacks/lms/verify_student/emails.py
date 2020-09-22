import warnings
warnings.warn("Importing verify_student.emails instead of lms.djangoapps.verify_student.emails is deprecated", stacklevel=2)

from lms.djangoapps.verify_student.emails import *
