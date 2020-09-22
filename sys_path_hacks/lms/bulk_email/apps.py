import warnings
warnings.warn("Importing bulk_email.apps instead of lms.djangoapps.bulk_email.apps is deprecated", stacklevel=2)

from lms.djangoapps.bulk_email.apps import *
