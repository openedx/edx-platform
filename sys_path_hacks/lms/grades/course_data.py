import warnings
warnings.warn("Importing grades.course_data instead of lms.djangoapps.grades.course_data is deprecated", stacklevel=2)

from lms.djangoapps.grades.course_data import *
