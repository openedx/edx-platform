import warnings
warnings.warn("Importing bulk_email.tasks instead of lms.djangoapps.bulk_email.tasks is deprecated", stacklevel=2)

from lms.djangoapps.bulk_email.tasks import *
