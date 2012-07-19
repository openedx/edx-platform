import pymongo

from nose.tools import assert_equals, assert_raises, assert_not_equals, with_setup
from path import path

from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import InvalidLocationError
from xmodule.modulestore.mongo import MongoModuleStore
from xmodule.modulestore.xml_importer import import_from_xml

# from ~/mitx_all/mitx/common/lib/xmodule/xmodule/modulestore/tests/
# to   ~/mitx_all/mitx/common/test
TEST_DIR = path(__file__).abspath().dirname()
for i in range(5):
    TEST_DIR = TEST_DIR.dirname()
TEST_DIR = TEST_DIR / 'test'

DATA_DIR = TEST_DIR / 'data'


HOST = 'localhost'
PORT = 27017
DB = 'test'
COLLECTION = 'modulestore'
FS_ROOT = DATA_DIR  # TODO (vshnayder): will need a real fs_root for testing load_item
DEFAULT_CLASS = 'xmodule.raw_module.RawDescriptor'


connection = None

def setup():
    global connection
    connection = pymongo.connection.Connection(HOST, PORT)
    


def setup_func():
    # connect to the db
    global store
    store = MongoModuleStore(HOST, DB, COLLECTION, FS_ROOT, default_class=DEFAULT_CLASS)
    print 'data_dir: {0}'.format(DATA_DIR)
    import_from_xml(store, DATA_DIR)
    
def teardown_func():
    global store
    store = None
    # Destroy the test db.
    connection.drop_database(DB)
    

@with_setup(setup_func, teardown_func)
def test_init():
    '''Just make sure the db loads'''
    pass
        
@with_setup(setup_func, teardown_func)
def test_get_courses():
    '''Make sure the course objects loaded properly'''
    courses = store.get_courses()
    print courses
        
