"""Constants used by PyFilesystem.
"""

import io


DEFAULT_CHUNK_SIZE = io.DEFAULT_BUFFER_SIZE * 16
"""`int`: the size of a single chunk read from or written to a file.
"""
