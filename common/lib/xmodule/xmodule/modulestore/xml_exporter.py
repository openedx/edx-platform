import logging
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from fs.osfs import OSFS
from json import dumps


def export_to_xml(modulestore, contentstore, course_location, root_dir, course_dir, draft_modulestore = None):

  course = modulestore.get_item(course_location)

  fs = OSFS(root_dir)
  export_fs = fs.makeopendir(course_dir)

  xml = course.export_to_xml(export_fs)
  with export_fs.open('course.xml', 'w') as course_xml:
      course_xml.write(xml)

  # export the static assets
  contentstore.export_all_for_course(course_location, root_dir + '/' + course_dir + '/static/')

  # export the static tabs
  export_extra_content(export_fs, modulestore, course_location, 'static_tab', 'tabs', '.html')

  # export the custom tags
  export_extra_content(export_fs, modulestore, course_location, 'custom_tag_template', 'custom_tags')

  # export the course updates
  export_extra_content(export_fs, modulestore, course_location, 'course_info', 'info', '.html')

  # export the grading policy
  policies_dir = export_fs.makeopendir('policies')
  course_run_policy_dir = policies_dir.makeopendir(course.location.name)
  if 'grading_policy' in course.definition['data']:
    with course_run_policy_dir.open('grading_policy.json', 'w') as grading_policy:
      grading_policy.write(dumps(course.definition['data']['grading_policy']))

  # export all of the course metadata in policy.json
  with course_run_policy_dir.open('policy.json', 'w') as course_policy:
    policy = {}
    policy = {'course/' + course.location.name: course.metadata}
    course_policy.write(dumps(policy)) 

  # export everything from the draft store, unfortunately this will create lots of duplicates
  if draft_modulestore is not None:
      draft_course = draft_modulestore.get_item(course_location)
      draft_course_dir = export_fs.makeopendir('drafts')
      xml = draft_course.export_to_xml(draft_course_dir)
      with draft_course_dir.open('course.xml', 'w') as course_xml:
        course_xml.write(xml)

  '''
  draft_items = modulestore.get_items([None, None, None, 'vertical', None, 'draft'])
  logging.debug('draft_items = {0}'.format(draft_items))
  if len(draft_items) > 0:
     
    for draft_item in draft_items:
      draft_item.export_to_xml(draft_items_dir)
    #with draft_items_dir.open(draft_item.location.name + '.xml', 'w'):
  '''    


def export_extra_content(export_fs, modulestore, course_location, category_type, dirname, file_suffix=''):
  query_loc = Location('i4x', course_location.org, course_location.course, category_type, None)
  items = modulestore.get_items(query_loc)

  if len(items) > 0:
    item_dir = export_fs.makeopendir(dirname)
    for item in items:
      with item_dir.open(item.location.name + file_suffix, 'w') as item_file:
        item_file.write(item.definition['data'].encode('utf8'))
