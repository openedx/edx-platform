import warnings
warnings.warn("Importing dashboard.management.commands.tests instead of lms.djangoapps.dashboard.management.commands.tests is deprecated", stacklevel=2)

from lms.djangoapps.dashboard.management.commands.tests import *
