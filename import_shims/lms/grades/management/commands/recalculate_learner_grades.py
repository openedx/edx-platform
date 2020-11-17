from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.management.commands.recalculate_learner_grades', 'lms.djangoapps.grades.management.commands.recalculate_learner_grades')

from lms.djangoapps.grades.management.commands.recalculate_learner_grades import *
