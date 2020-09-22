import warnings
warnings.warn("Importing certificates.management.commands.ungenerated_certs instead of lms.djangoapps.certificates.management.commands.ungenerated_certs is deprecated", stacklevel=2)

from lms.djangoapps.certificates.management.commands.ungenerated_certs import *
