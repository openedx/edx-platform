import warnings
warnings.warn("Importing certificates.management.commands.regenerate_user instead of lms.djangoapps.certificates.management.commands.regenerate_user is deprecated", stacklevel=2)

from lms.djangoapps.certificates.management.commands.regenerate_user import *
