import warnings
warnings.warn("Importing certificates.management.commands.gen_cert_report instead of lms.djangoapps.certificates.management.commands.gen_cert_report is deprecated", stacklevel=2)

from lms.djangoapps.certificates.management.commands.gen_cert_report import *
