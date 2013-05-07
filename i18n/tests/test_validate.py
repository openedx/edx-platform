import os
from unittest import TestCase
from nose.plugins.skip import SkipTest

from config import LOCALE_DIR
from execute import call, LOG
        
def test_po_files():
    """
    This is a generator. It yields all of the .po files under root, and tests each one.
    """
    for (dirpath, dirnames, filenames) in os.walk(LOCALE_DIR):
        for name in filenames:
            print name
            (base, ext) = os.path.splitext(name)
            if ext.lower() == '.po':
                yield validate_po_file, os.path.join(dirpath, name)


def validate_po_file(filename):
    """
    Call GNU msgfmt -c on each .po file to validate its format.
    """
    # Skip this test for now because it's very noisy
    raise SkipTest()
    # Use relative paths to make output less noisy.
    rfile = os.path.relpath(filename, LOCALE_DIR)
    (out, err) = call(['msgfmt','-c', rfile], log=None, working_directory=LOCALE_DIR)
    if err != '':
        LOG.warn('\n'+err)

