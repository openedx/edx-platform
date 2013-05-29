from django.core.files.uploadhandler import FileUploadHandler
import time


class DebugFileUploader(FileUploadHandler):
    def receive_data_chunk(self, raw_data, start):
        time.sleep(1)
        return raw_data

    def file_complete(self, file_size):
        return None
