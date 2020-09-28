import warnings
warnings.warn("Importing grades.subsection_grade instead of lms.djangoapps.grades.subsection_grade is deprecated", stacklevel=2)

from lms.djangoapps.grades.subsection_grade import *
