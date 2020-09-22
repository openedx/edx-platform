import warnings
warnings.warn("Importing grades.course_grade instead of lms.djangoapps.grades.course_grade is deprecated", stacklevel=2)

from lms.djangoapps.grades.course_grade import *
