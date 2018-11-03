"""

Implements a thread pool for parallel copying of files.

"""

from __future__ import unicode_literals

import threading

if False:  # typing.TYPE_CHECKING
    from types import TracebackType
    from typing import (
        Iterator, Optional, Mapping, Text, Type, Union)


from six.moves.queue import Queue

from .tools import copy_file_data


class _Worker(threading.Thread):
    """Worker thread that pulls tasks from a queue."""

    def __init__(self, copier):
        self.copier = copier
        super(_Worker, self).__init__()
        self.daemon = True

    def run(self):
        queue = self.copier.queue
        while True:
            task = queue.get(block=True)
            try:
                if task is None:
                    break
                task()
            except Exception as error:
                self.copier.add_error(error)
            finally:
                queue.task_done()


class _CopyTask(object):
    """A callable that copies from one file another."""
    def __init__(self, src_file, dst_file):
        self.src_file = src_file
        self.dst_file = dst_file

    def __repr__(self):
        return 'CopyTask(%r, %r)'.format(
            self.src_file,
            self.dst_file,
        )

    def __call__(self):
        try:
            copy_file_data(
                self.src_file, self.dst_file, chunk_size=1024 * 1024
            )
        finally:
            try:
                self.src_file.close()
            finally:
                self.dst_file.close()


class Copier(object):
    def __init__(self, num_workers=4):
        self.num_workers = num_workers
        self.queue = None
        self.workers = []
        self.errors = []
        self.running = False

    def start(self):
        if self.num_workers:
            self.queue = Queue(maxsize=self.num_workers)
            self.workers = [
                _Worker(self) for _ in range(self.num_workers)
            ]
            for worker in self.workers:
                worker.start()
        self.running = True

    def stop(self):
        if self.running and self.num_workers:
            for worker in self.workers:
                self.queue.put(None)
            for worker in self.workers:
                worker.join()
            self.queue.join()
        self.running = False

    def add_error(self, error):
        self.errors.append(error)

    def __enter__(self):
        self.start()
        return self

    def __exit__(
        self,
        exc_type,      # type: Optional[Type[BaseException]]
        exc_value,     # type: Optional[BaseException]
        traceback      # type: Optional[TracebackType]
    ):
        self.stop()

    def copy(self, src_fs, src_path, dst_fs, dst_path):
        """Copy a file from on fs to another."""
        src_file = src_fs.openbin(src_path, 'r')
        try:
            dst_file = dst_fs.openbin(dst_path, 'w')
        except Exception:
            # If dst file fails to open, explicitly close src_file
            src_file.close()
            raise
        task = _CopyTask(src_file, dst_file)
        if self.num_workers:
            self.queue.put(task)
        else:
            task()
