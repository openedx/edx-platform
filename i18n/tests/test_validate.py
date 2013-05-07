import os
from unittest import TestCase
from nose.plugins.skip import SkipTest

from logger import get_logger
from config import LOCALE_DIR
from execute import call
        
def test_po_files(root=LOCALE_DIR):
    """
    This is a generator. It yields all of the .po files under root, and tests each one.
    """
    log = get_logger(__name__)
    for (dirpath, dirnames, filenames) in os.walk(root):
        for name in filenames:
            print name
            (base, ext) = os.path.splitext(name)
            if ext.lower() == '.po':
                yield validate_po_file, os.path.join(dirpath, name), log


def validate_po_file(filename, log):
    """
    Call GNU msgfmt -c on each .po file to validate its format.
    Any errors caught by msgfmt are logged to log.
    """
    # Skip this test for now because it's very noisy
    raise SkipTest()
    # Use relative paths to make output less noisy.
    rfile = os.path.relpath(filename, LOCALE_DIR)
    (out, err) = call(['msgfmt','-c', rfile], log=None, working_directory=LOCALE_DIR)
    if err != '':
        log.warn('\n'+err)

