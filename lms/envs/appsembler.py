from .aws import *

GOOGLE_TAG_MANAGER_ID = os.environ.get("GOOGLE_TAG_MANAGER_ID", None)

INSTALLED_APPS += ('appsembler',)
