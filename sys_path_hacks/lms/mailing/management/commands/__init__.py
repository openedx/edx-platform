import warnings
warnings.warn("Importing mailing.management.commands instead of lms.djangoapps.mailing.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.mailing.management.commands import *
