import warnings
warnings.warn("Importing grades.course_grade_factory instead of lms.djangoapps.grades.course_grade_factory is deprecated", stacklevel=2)

from lms.djangoapps.grades.course_grade_factory import *
