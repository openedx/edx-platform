import io

from django.test import TestCase

from util import csv_processor


class DummyProcessor(csv_processor.CSVProcessor):
    columns = ['foo', 'bar']

    def process_row(self, row):
        undo = row.copy()
        undo['undo'] = True
        return True, undo


class CSVTestCase(TestCase):
    def test_write(self):
        pass

    def test_read(self):
        pass

    def test_commit(self):
        pass

    def test_rollback(self):
        pass



