from path import path

# from ~/mitx_all/mitx/common/lib/xmodule/xmodule/modulestore/tests/
# to   ~/mitx_all/mitx/common/test
TEST_DIR = path(__file__).abspath().dirname()
for i in range(5):
    TEST_DIR = TEST_DIR.dirname()
TEST_DIR = TEST_DIR / 'test'

DATA_DIR = TEST_DIR / 'data'


