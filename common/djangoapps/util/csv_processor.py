"""
"""
from __future__ import unicode_literals, print_function
import csv
import hashlib
import importlib
import json
import logging

from celery import task
from celery.result import AsyncResult
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.translation import ugettext_lazy as _

log = logging.getLogger(__name__)


class CSVProcessor(object):
    """
    Generic CSV processor.

    Create a subclass that implements process_row(row)

    To use:
    processor = MyProcessor(optional_args='foo')
    processor.process_file(open_csv_file)
    result = processor.status()

    If you want to separate validation/processing:
    processor = MyProcessor(optional_args='foo')
    processor.process_file(open_csv_file, autocommit=False)
    # save the state somewhere, or send to another process.
    processor.commit()

    If the subclass saves rows to self.rollback_rows, it's possible to
    rollback the saved items by calling processor.rollback()
    """
    columns = []
    required_columns = []
    max_file_size = 2 * 1024 * 1024

    def __init__(self, **kwargs):
        self.total_rows = 0
        self.processed_rows = 0
        self.saved_rows = 0
        self.stage = []
        self.rollback_rows = []
        self.rowerrors = []
        self.error_messages = {}
        for key, value in kwargs.items():
            setattr(self, key, value)

    def add_error(self, message):
        """
        Add an error message. Does not store duplicates.
        """
        self.error_messages.setdefault(message, 1)

    def write_file(self, thefile, rows=None):
        """
        Write the rows to the file.
        """
        rows = rows or self.get_rows_to_export()
        writer = csv.DictWriter(thefile, self.columns)
        writer.writeheader()
        for row in rows:
            self.preprocess_export_row(row)
            writer.writerow(row)

    def process_file(self, thefile, autocommit=True):
        """
        Read the file, validating and preprocessing each row.
        If autocommit=False, rows will be staged for writing. Call commit() to finalize.
        If autocommit=True, the staged rows will be committed.
        """
        reader = self.read_file(thefile)
        if reader:
            self.preprocess_file(reader)
            thefile.close()
            if autocommit and self.can_commit:
                self.commit()

    def read_file(self, thefile):
        """
        Create a CSV reader and validate the file.
        Returns the reader.
        """
        reader = csv.DictReader(thefile)
        if not self.validate_file(thefile, reader):
            return
        return reader

    def preprocess_file(self, reader):
        """
        Preprocess the rows, saving them to the staging list.
        """
        rownum = processed_rows = 0
        for rownum, row in enumerate(reader, 1):
            if self.validate_row(row):
                row = self.preprocess_row(row)
                if row:
                    self.stage.append(row)
                    processed_rows += 1
            else:
                self.rowerrors.append(rownum)
        self.total_rows = rownum
        self.processed_rows = processed_rows

    def validate_file(self, thefile, reader):
        """
        Validate the file.
        Returns bool.
        """
        if hasattr(thefile, 'size') and self.max_file_size and thefile.size > self.max_file_size:
            self.add_error(_("The CSV file must be under {} bytes").format(self.max_file_size))
            return False
        elif self.required_columns:
            for field in self.required_columns:
                if field not in reader.fieldnames:
                    self.add_error(_("Missing column: {}").format(field))
                    return False
        return True

    def validate_row(self, row):
        """
        Validate the fields in the row.
        Returns bool.
        """
        return True

    def preprocess_export_row(self, row):
        """
        Preprocess row just before writing to CSV.
        Returns a row.
        """

    def preprocess_row(self, row):
        """
        Preprocess the row.
        Returns the same row or new row, or None.
        """
        return row

    def get_rows_to_export(self):
        """
        Subclasses should implement this to return rows to export.
        """
        return []

    @property
    def can_commit(self):
        """
        Return whether there's data to commit.
        """
        return bool(self.stage and not self.rowerrors)

    def commit(self):
        """
        Commit the processed rows to the database.
        """
        saved = 0
        while self.stage:
            row = self.stage.pop(0)
            try:
                did_save, rollback_row = self.process_row(row)
                if did_save:
                    saved += 1
                    if rollback_row:
                        self.rollback_rows.append(rollback_row)
            except Exception as e:
                log.exception('Committing %r', self)
                self.add_error(str(e))
        self.saved_rows = saved
        log.info('%r committed %d rows', self, saved)

    def rollback(self):
        """
        Rollback the previously saved rows, by applying each undo row.
        """
        saved = 0
        while self.rollback_rows:
            row = self.rollback_rows.pop(0)
            try:
                did_save, __ = self.process_row(row)
                if did_save:
                    saved += 1
            except Exception as e:
                log.exception('Rolling back %r', self)
                self.add_error(str(e))
        self.saved_rows = saved

    def status(self):
        """
        Return a status dict.
        """
        result = {
            'total': self.total_rows,
            'processed': self.processed_rows,
            'saved': self.saved_rows,
            'error_rows': self.rowerrors,
            'error_messages': list(self.error_messages.keys()),
            'percentage': format(self.saved_rows / float(self.total_rows or 1), '.1%'),
            'can_commit': self.can_commit,
        }
        return result

    def process_row(self, row):
        """
        Save the row to the database.
        Returns success, undo (dictionary of row to use for rolling back the operation) or None

        At minimun should implement this method.
        """
        return False, None


class ChecksumMixin(object):
    """
    CSV mixin that will create and verify a checksum column in the CSV file
    Specify a list checksum_columns in the subclass.
    """
    secret = settings.SECRET_KEY
    checksum_columns = []
    checksum_fieldname = 'csum'
    checksum_size = 4

    def _get_checksum(self, row):
        to_check = ''.join(str(row[key] or '') for key in self.checksum_columns)
        to_check += self.secret
        return hashlib.md5(to_check).hexdigest()[:self.checksum_size]

    def preprocess_export_row(self, row):
        """
        Set the checksum column in the row.
        """
        row[self.checksum_fieldname] = self._get_checksum(row)

    def validate_row(self, row):
        """
        Verifies that the calculated checksum matches the stored checksum.
        """
        return self._get_checksum(row) == row[self.checksum_fieldname]


@task(bind=True)
def do_deferred_commit(self, state_file):
    log.info('Loading CSV state %s', state_file)
    with default_storage.open(state_file, 'r') as statefile:
        state = json.loads(statefile.read())
    module_name, classname = state.pop('__class__')

    instance = getattr(importlib.import_module(module_name), classname)(**state)
    instance.commit(running_task=True)
    status = instance.status()
    log.info('Commit succeeded %r %s', instance, status)
    filename = instance.save()
    log.info('Saved CSV state %r %s', instance, filename)
    return status


class DeferrableMixin(object):
    """
    Mixin that automatically commits data using celery.

    Subclasses should specify `size_to_defer` to tune when to
    run the commit synchronously or asynchronously

    Subclasses must override get_unique_path to uniquely identify
    this task
    """
    # if the number of rows is greater than size_to_defer,
    # run the task asynchonously. Otherwise, commit immediately.
    # 0 means: always run in a celery task
    size_to_defer = 0

    def get_unique_path(self):
        raise NotImplementedError()

    def save(self):
        """
        Save the state of this object to django storage.
        """
        state = self.__dict__.copy()
        for k, v in state.items():
            if isinstance(v, set):
                state[k] = list(v)
        state['__class__'] = (self.__class__.__module__, self.__class__.__name__)
        return default_storage.save(self.get_unique_path(), ContentFile(json.dumps(state)))

    @classmethod
    def get_deferred_result(cls, result_id):
        """
        Return the celery result for the given id.
        """
        return AsyncResult(result_id)

    def status(self):
        status = super(DeferrableMixin, self).status()
        status['result_id'] = getattr(self, 'result_id', None)
        status['waiting'] = bool(status['result_id'])
        return status

    def commit(self, running_task=None):
        """
        Automatically defer the commit to a celery task
        if the number of rows is greater than self.size_to_defer
        """
        if running_task or len(self.stage) <= self.size_to_defer:
            # called by the async task
            # or small enough to commit now
            super(DeferrableMixin, self).commit()
        else:
            # run asynchronously
            filename = self.save()
            result = do_deferred_commit.delay(filename)
            self.result_id = result.id
            log.info('Queued task %s %r', filename, result)
