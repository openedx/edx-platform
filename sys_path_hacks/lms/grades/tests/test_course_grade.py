import warnings
warnings.warn("Importing grades.tests.test_course_grade instead of lms.djangoapps.grades.tests.test_course_grade is deprecated", stacklevel=2)

from lms.djangoapps.grades.tests.test_course_grade import *
