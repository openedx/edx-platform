from nose.tools import assert_equals, assert_raises, assert_not_equals, with_setup
from xmodule.modulestore import Location
from xmodule.modulestore.exceptions import InvalidLocationError
from xmodule.modulestore.mongo import MongoModuleStore


host = 'localhost'
db = 'xmodule'
collection = 'modulestore'
fs_root = None  # TODO (vshnayder): will need a real fs_root for testing load_item
default_class = 'xmodule.raw_module.RawDescriptor'



def setup_func():
    # connect to the db
    global store
    store = MongoModuleStore(host, db, collection, fs_root, default_class=default_class)
    
def teardown_func():
    global store
    store = None

@with_setup(setup_func, teardown_func)
def test_init():
    '''Just make sure the db loads'''
    pass
        
