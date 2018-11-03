from base64 import decodestring
import json
from unittest import TestCase

from ipython_genutils.py3compat import unicode_type
from ..nbjson import reads, writes
from .. import nbjson
from .nbexamples import nb0

from . import formattest


class TestJSON(formattest.NBFormatTest, TestCase):

    nb0_ref = None
    ext = 'ipynb'
    mod = nbjson

    def test_roundtrip_nosplit(self):
        """Ensure that multiline blobs are still readable"""
        # ensures that notebooks written prior to splitlines change
        # are still readable.
        s = writes(nb0, split_lines=False)
        self.assertEqual(nbjson.reads(s),nb0)

    def test_roundtrip_split(self):
        """Ensure that splitting multiline blocks is safe"""
        # This won't differ from test_roundtrip unless the default changes
        s = writes(nb0, split_lines=True)
        self.assertEqual(nbjson.reads(s),nb0)
    
    def test_splitlines(self):
        """Test splitlines in mime-bundles"""
        s = writes(nb0, split_lines=True)
        raw_nb = json.loads(s)

        for i, ref_cell in enumerate(nb0.cells):
            if ref_cell.source.strip() == 'Cell with attachments':
                attach_ref = ref_cell['attachments']['attachment1']
                attach_json = raw_nb['cells'][i]['attachments']['attachment1']
            if ref_cell.source.strip() == 'json_outputs()':
                output_ref = ref_cell['outputs'][0]['data']
                output_json = raw_nb['cells'][i]['outputs'][0]['data']

        for key, json_value in attach_json.items():
            if key == 'text/plain':
                # text should be split
                assert json_value == attach_ref['text/plain'].splitlines(True)
            else:
                # JSON attachments
                assert json_value == attach_ref[key]

        # check that JSON outputs are left alone:
        for key, json_value in output_json.items():
            if key == 'text/plain':
                # text should be split
                assert json_value == output_ref['text/plain'].splitlines(True)
            else:
                # JSON outputs should be left alone
                assert json_value == output_ref[key]

    def test_read_png(self):
        """PNG output data is b64 unicode"""
        s = writes(nb0)
        nb1 = nbjson.reads(s)
        found_png = False
        for cell in nb1.cells:
            if not 'outputs' in cell:
                continue
            for output in cell.outputs:
                if not 'data' in output:
                    continue
                if 'image/png' in output.data:
                    found_png = True
                    pngdata = output.data['image/png']
                    self.assertEqual(type(pngdata), unicode_type)
                    # test that it is valid b64 data
                    b64bytes = pngdata.encode('ascii')
                    raw_bytes = decodestring(b64bytes)
        assert found_png, "never found png output"

    def test_read_jpeg(self):
        """JPEG output data is b64 unicode"""
        s = writes(nb0)
        nb1 = nbjson.reads(s)
        found_jpeg = False
        for cell in nb1.cells:
            if not 'outputs' in cell:
                continue
            for output in cell.outputs:
                if not 'data' in output:
                    continue
                if 'image/jpeg' in output.data:
                    found_jpeg = True
                    jpegdata = output.data['image/jpeg']
                    self.assertEqual(type(jpegdata), unicode_type)
                    # test that it is valid b64 data
                    b64bytes = jpegdata.encode('ascii')
                    raw_bytes = decodestring(b64bytes)
        assert found_jpeg, "never found jpeg output"
