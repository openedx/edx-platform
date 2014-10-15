from .aws import *
from .edraak_common import *

SESSION_COOKIE_DOMAIN = ".edraak.org"
LMS_BASE = "edraak.org"
STATIC_ROOT_BASE = "/edx/var/edxapp/staticfiles",
STATIC_URL_BASE = "https://d2q9s3qze1y77b.cloudfront.net/static/",

GRADES_DOWNLOAD = {
    "BUCKET": FILE_UPLOAD_STORAGE_BUCKET_NAME,
    "ROOT_PATH": "edraak",
    "STORAGE_TYPE": "s3"
}
