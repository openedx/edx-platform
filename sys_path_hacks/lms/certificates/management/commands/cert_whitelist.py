import warnings
warnings.warn("Importing certificates.management.commands.cert_whitelist instead of lms.djangoapps.certificates.management.commands.cert_whitelist is deprecated", stacklevel=2)

from lms.djangoapps.certificates.management.commands.cert_whitelist import *
