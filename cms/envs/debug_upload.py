"""
A new cms ENV configuration to use a slow upload file handler to help test
progress bars in uploads
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from .dev import *

FILE_UPLOAD_HANDLERS = [
    'contentstore.debug_file_uploader.DebugFileUploader',
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]
