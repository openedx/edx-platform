"""
Tests for CSVProcessor
"""
from __future__ import absolute_import, print_function, unicode_literals

import io

import ddt
# could use BytesIO, but this adds a size attribute
from django.core.files.base import ContentFile
from django.test import TestCase

from util import csv_processor


class DummyProcessor(csv_processor.CSVProcessor):
    max_file_size = 20
    columns = ['foo', 'bar']
    required_columns = ['foo', 'bar']

    def get_rows_to_export(self):
        for row in super(DummyProcessor, self).get_rows_to_export():
            yield row
        yield {'foo': 1, 'bar': 1}
        yield {'foo': 2, 'bar': 2}

    def validate_row(self, row):
        return super(DummyProcessor, self).validate_row(row) and row['foo'] != '3'

    def process_row(self, row):
        if row['foo'] == '4':
            raise ValueError('4 is not allowed')
        undo = row.copy()
        undo['undo'] = True
        if row['foo'] == '2':
            undo['foo'] = '4'
        return True, undo


class DummyChecksumProcessor(csv_processor.ChecksumMixin, DummyProcessor):
    checksum_columns = ['foo', 'bar']


class DummyDeferrableProcessor(csv_processor.DeferrableMixin, DummyProcessor):
    size_to_defer = 1

    def get_unique_path(self):
        return 'csv/test'


@ddt.ddt
class CSVTestCase(TestCase):
    def setUp(self):
        super(CSVTestCase, self).setUp()
        self.dummy_csv = b'foo,bar\r\n1,1\r\n2,2\r\n'

    def test_write(self):
        buf = io.BytesIO()
        processor = DummyProcessor(dummy_arg=True)
        assert processor.dummy_arg is True
        processor.write_file(buf)
        data = buf.getvalue()
        assert data == self.dummy_csv

    def test_read(self):
        buf = ContentFile(self.dummy_csv)
        processor = DummyProcessor()
        processor.process_file(buf)
        status = processor.status()
        assert status['saved'] == 2
        assert status['processed'] == 2

    @ddt.data(
        (b'foo,baz\r\n', None, 'Missing column: bar'),
        (b'foo,bar\r\n1,2\r\n3,3\r\n', [2], None),
        (b'foo,bar\r\n1,2\r\n4,4\r\n', [], '4 is not allowed'),
        (b'foo,bar\r\n1,2\r\n4,4\r\n5,5\r\n', [], 'The CSV file must be under 20 bytes'),
    )
    @ddt.unpack
    def test_file_errors(self, contents, error_rows, message):
        processor = DummyProcessor()
        processor.process_file(ContentFile(contents))
        status = processor.status()
        if error_rows:
            assert status["error_rows"] == error_rows
        if message:
            assert status["error_messages"][0] == message

    def test_checksum(self):
        processor = DummyChecksumProcessor()
        row = {
            'foo': 1,
            'bar': b'hello',
        }
        processor.preprocess_export_row(row)
        assert row['csum'] == 'bc90'
        assert processor.validate_row(row)
        row['csum'] = 'def'
        assert not processor.validate_row(row)

    def test_rollback(self):
        processor = DummyProcessor()
        processor.process_file(ContentFile(self.dummy_csv))
        assert processor.status()['saved'] == 2
        processor.rollback()
        status = processor.status()
        assert status['saved'] == 1
        assert status['error_messages'][0] == '4 is not allowed'

    def test_defer(self):
        processor = DummyDeferrableProcessor()
        processor.test_set = set((1, 2, 3))
        processor.process_file(ContentFile(self.dummy_csv))
        status = processor.status()
        assert status['waiting']
        result_id = status['result_id']
        results = processor.get_deferred_result(result_id)
        assert results

    def test_defer_too_small(self):
        processor = DummyDeferrableProcessor()
        processor.process_file(ContentFile(b'foo,bar\r\n1,2\r\n'))
        status = processor.status()
        assert not status['waiting']
