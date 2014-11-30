"""
A new cms ENV configuration to use a slow upload file handler to help test
progress bars in uploads
"""
# pylint: disable=W0614, W0401
from .dev import *

FILE_UPLOAD_HANDLERS = (
    'contentstore.debug_file_uploader.DebugFileUploader',
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)
