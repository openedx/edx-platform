import warnings
warnings.warn("Importing verify_student.apps instead of lms.djangoapps.verify_student.apps is deprecated", stacklevel=2)

from lms.djangoapps.verify_student.apps import *
