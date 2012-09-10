from xmodule.modulestore import Location
from xmodule.modulestore.xml import XMLModuleStore
from xmodule.modulestore.xml_importer import import_from_xml

from .test_modulestore import check_path_to_location
from . import DATA_DIR

class TestXMLModuleStore(object):
    def test_path_to_location(self):
        """Make sure that path_to_location works properly"""

        print "Starting import"
        modulestore = XMLModuleStore(DATA_DIR, course_dirs=['toy', 'simple'])
        print "finished import"
        
        check_path_to_location(modulestore)
