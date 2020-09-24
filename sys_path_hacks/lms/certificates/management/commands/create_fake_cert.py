import warnings
warnings.warn("Importing certificates.management.commands.create_fake_cert instead of lms.djangoapps.certificates.management.commands.create_fake_cert is deprecated", stacklevel=2)

from lms.djangoapps.certificates.management.commands.create_fake_cert import *
