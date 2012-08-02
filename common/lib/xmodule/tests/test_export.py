from xmodule.modulestore.xml import XMLModuleStore
from nose.tools import assert_equals
from nose import SkipTest
from tempfile import mkdtemp
from fs.osfs import OSFS


def check_export_roundtrip(data_dir):
    print "Starting import"
    initial_import = XMLModuleStore('org', 'course', data_dir, eager=True)
    initial_course = initial_import.course

    print "Starting export"
    export_dir = mkdtemp()
    fs = OSFS(export_dir)
    xml = initial_course.export_to_xml(fs)
    with fs.open('course.xml', 'w') as course_xml:
        course_xml.write(xml)

    print "Starting second import"
    second_import = XMLModuleStore('org', 'course', export_dir, eager=True)

    print "Checking key equality"
    assert_equals(initial_import.modules.keys(), second_import.modules.keys())

    print "Checking module equality"
    for location in initial_import.modules.keys():
        print "Checking", location
        assert_equals(initial_import.modules[location], second_import.modules[location])


def test_toy_roundtrip():
    dir = ""
    # TODO: add paths and make this run.
    raise SkipTest()
    check_export_roundtrip(dir)
