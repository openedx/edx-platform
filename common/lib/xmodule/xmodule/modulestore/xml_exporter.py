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

  # export the static tabs
  static_tabs_query_loc = Location('i4x', course_location.org, course_location.course, 'static_tab', None)
  static_tabs = modulestore.get_items(static_tabs_query_loc)

  if len(static_tabs) > 0:
    tab_dir = export_fs.makeopendir('tabs')
    for tab in static_tabs:
      with tab_dir.open(tab.location.name + '.html', 'w') as tab_file:
        tab_file.write(tab.definition['data'].encode('utf8'))

  # export custom tags
  custom_tags_query_loc = Location('i4x', course_location.org, course_location.course, 'custom_tag_template', None)
  custom_tags = modulestore.get_items(custom_tags_query_loc)

  if len(custom_tags) > 0:
    tab_dir = export_fs.makeopendir('custom_tags')
    for tag in custom_tags:
      with tab_dir.open(tag.location.name, 'w') as tag_file:
        tag_file.write(tag.definition['data'].encode('utf8')) 



  