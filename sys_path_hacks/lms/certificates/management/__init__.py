import warnings
warnings.warn("Importing certificates.management instead of lms.djangoapps.certificates.management is deprecated", stacklevel=2)

from lms.djangoapps.certificates.management import *
