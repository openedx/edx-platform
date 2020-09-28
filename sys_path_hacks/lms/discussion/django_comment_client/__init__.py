import warnings
warnings.warn("Importing discussion.django_comment_client instead of lms.djangoapps.discussion.django_comment_client is deprecated", stacklevel=2)

from lms.djangoapps.discussion.django_comment_client import *
