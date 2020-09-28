import warnings
warnings.warn("Importing grades.management.commands.recalculate_learner_grades instead of lms.djangoapps.grades.management.commands.recalculate_learner_grades is deprecated", stacklevel=2)

from lms.djangoapps.grades.management.commands.recalculate_learner_grades import *
