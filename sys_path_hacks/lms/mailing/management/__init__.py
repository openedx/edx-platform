import warnings
warnings.warn("Importing mailing.management instead of lms.djangoapps.mailing.management is deprecated", stacklevel=2)

from lms.djangoapps.mailing.management import *
