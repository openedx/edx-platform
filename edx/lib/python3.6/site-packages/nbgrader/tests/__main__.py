import sys
import os
import pytest
testdir = os.path.dirname(__file__)
pytest.main(sys.argv[1:] + [testdir])
