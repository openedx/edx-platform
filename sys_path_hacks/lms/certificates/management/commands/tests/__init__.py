import warnings
warnings.warn("Importing certificates.management.commands.tests instead of lms.djangoapps.certificates.management.commands.tests is deprecated", stacklevel=2)

from lms.djangoapps.certificates.management.commands.tests import *
