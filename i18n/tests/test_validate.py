import os
from unittest import TestCase
from nose.plugins.skip import SkipTest

from config import LOCALE_DIR
from execute import call, LOG

class TestValidate(TestCase):
    """
    Call GNU msgfmt -c on each .po file to validate its format.
    """
        
    def test_validate(self):
        # Skip this test for now because it's very noisy
        raise SkipTest()
        for file in self.get_po_files():
            # Use relative paths to make output less noisy.
            rfile = os.path.relpath(file, LOCALE_DIR)
            (out, err) = call(['msgfmt','-c', rfile], log=None, working_directory=LOCALE_DIR)
            if err != '':
                LOG.warn('\n'+err)

    def get_po_files(self, root=LOCALE_DIR):
        """
        This is a generator. It yields all of the .po files under root.
        """
        for (dirpath, dirnames, filenames) in os.walk(root):
            for name in filenames:
                (base, ext) = os.path.splitext(name)
                if ext.lower() == '.po':
                    yield os.path.join(dirpath, name)


    
