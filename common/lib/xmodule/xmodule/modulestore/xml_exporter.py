import logging
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from fs.osfs import OSFS

def export_to_xml(modulestore, contentstore, course_location, root_dir, course_dir):

  course = modulestore.get_item(course_location)

  fs = OSFS(root_dir)
  export_fs = fs.makeopendir(course_dir)

  xml = course.export_to_xml(export_fs)
  with export_fs.open('course.xml', 'w') as course_xml:
      course_xml.write(xml)

  # export the static assets
  contentstore.export_all_for_course(course_location, root_dir + '/' + course_dir + '/static/')

  