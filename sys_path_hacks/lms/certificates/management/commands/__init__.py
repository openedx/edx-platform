import warnings
warnings.warn("Importing certificates.management.commands instead of lms.djangoapps.certificates.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.certificates.management.commands import *
