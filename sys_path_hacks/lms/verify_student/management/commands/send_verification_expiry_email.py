import warnings
warnings.warn("Importing verify_student.management.commands.send_verification_expiry_email instead of lms.djangoapps.verify_student.management.commands.send_verification_expiry_email is deprecated", stacklevel=2)

from lms.djangoapps.verify_student.management.commands.send_verification_expiry_email import *
