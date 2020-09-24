import warnings
warnings.warn("Importing verify_student.urls instead of lms.djangoapps.verify_student.urls is deprecated", stacklevel=2)

from lms.djangoapps.verify_student.urls import *
