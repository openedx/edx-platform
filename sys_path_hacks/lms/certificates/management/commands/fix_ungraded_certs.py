import warnings
warnings.warn("Importing certificates.management.commands.fix_ungraded_certs instead of lms.djangoapps.certificates.management.commands.fix_ungraded_certs is deprecated", stacklevel=2)

from lms.djangoapps.certificates.management.commands.fix_ungraded_certs import *
