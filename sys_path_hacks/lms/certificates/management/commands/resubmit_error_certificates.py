import warnings
warnings.warn("Importing certificates.management.commands.resubmit_error_certificates instead of lms.djangoapps.certificates.management.commands.resubmit_error_certificates is deprecated", stacklevel=2)

from lms.djangoapps.certificates.management.commands.resubmit_error_certificates import *
