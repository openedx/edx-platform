from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.management.commands.tests.test_recalculate_learner_grades')

from lms.djangoapps.grades.management.commands.tests.test_recalculate_learner_grades import *
