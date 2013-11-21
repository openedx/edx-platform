"""
Methods for exporting course data to XML
"""

import logging
from xmodule.modulestore import Location
from xmodule.modulestore.inheritance import own_metadata
from fs.osfs import OSFS
from json import dumps
import json
import datetime

#from django.utils.functional import Promise
#from django.utils.encoding import force_unicode


class EdxJSONEncoder(json.JSONEncoder):
    """
    Custom JSONEncoder that handles `Location` and `datetime.datetime` objects.

    `Location`s are encoded as their url string form, and `datetime`s as
    ISO date strings
    """
    def default(self, obj):
       # if isinstance(obj, Promise):
       #     return force_unicode(obj)
        if isinstance(obj, Location):
            return obj.url()
        elif isinstance(obj, datetime.datetime):
            if obj.tzinfo is not None:
                if obj.utcoffset() is None:
                    return obj.isoformat() + 'Z'
                else:
                    return obj.isoformat()
            else:
                return obj.isoformat()
        else:
            return super(EdxJSONEncoder, self).default(obj)


def export_to_xml(modulestore, contentstore, course_location, root_dir, course_dir, draft_modulestore=None):
    """
    Export all modules from `modulestore` and content from `contentstore` as xml to `root_dir`.

    `modulestore`: A `ModuleStore` object that is the source of the modules to export
    `contentstore`: A `ContentStore` object that is the source of the content to export, can be None
    `course_location`: The `Location` of the `CourseModuleDescriptor` to export
    `root_dir`: The directory to write the exported xml to
    `course_dir`: The name of the directory inside `root_dir` to write the course content to
    `draft_modulestore`: An optional `DraftModuleStore` that contains draft content, which will be exported
        alongside the public content in the course.
    """

    course_id = course_location.course_id
    course = modulestore.get_course(course_id)

    fs = OSFS(root_dir)
    export_fs = fs.makeopendir(course_dir)

    xml = course.export_to_xml(export_fs)
    with export_fs.open('course.xml', 'w') as course_xml:
        course_xml.write(xml)

    # export the static assets
    policies_dir = export_fs.makeopendir('policies')
    if contentstore:
        contentstore.export_all_for_course(
            course_location,
            root_dir + '/' + course_dir + '/static/',
            root_dir + '/' + course_dir + '/policies/assets.json',
        )

    # export the static tabs
    export_extra_content(export_fs, modulestore, course_id, course_location, 'static_tab', 'tabs', '.html')

    # export the custom tags
    export_extra_content(export_fs, modulestore, course_id, course_location, 'custom_tag_template', 'custom_tags')

    # export the course updates
    export_extra_content(export_fs, modulestore, course_id, course_location, 'course_info', 'info', '.html')

    # export the 'about' data (e.g. overview, etc.)
    export_extra_content(export_fs, modulestore, course_id, course_location, 'about', 'about', '.html')

    # export the grading policy
    course_run_policy_dir = policies_dir.makeopendir(course.location.name)
    with course_run_policy_dir.open('grading_policy.json', 'w') as grading_policy:
        grading_policy.write(dumps(course.grading_policy, cls=EdxJSONEncoder))

    # export all of the course metadata in policy.json
    with course_run_policy_dir.open('policy.json', 'w') as course_policy:
        policy = {'course/' + course.location.name: own_metadata(course)}
        course_policy.write(dumps(policy, cls=EdxJSONEncoder))

    # export draft content
    # NOTE: this code assumes that verticals are the top most draftable container
    # should we change the application, then this assumption will no longer
    # be valid
    if draft_modulestore is not None:
        draft_verticals = draft_modulestore.get_items([None, course_location.org, course_location.course,
                                                       'vertical', None, 'draft'])
        if len(draft_verticals) > 0:
            draft_course_dir = export_fs.makeopendir('drafts')
            for draft_vertical in draft_verticals:
                if getattr(draft_vertical, 'is_draft', False):
                    parent_locs = draft_modulestore.get_parent_locations(draft_vertical.location, course.location.course_id)
                    # Don't try to export orphaned items.
                    if len(parent_locs) > 0:
                        logging.debug('parent_locs = {0}'.format(parent_locs))
                        draft_vertical.xml_attributes['parent_sequential_url'] = Location(parent_locs[0]).url()
                        sequential = modulestore.get_item(Location(parent_locs[0]))
                        index = sequential.children.index(draft_vertical.location.url())
                        draft_vertical.xml_attributes['index_in_children_list'] = str(index)
                        draft_vertical.export_to_xml(draft_course_dir)


def export_extra_content(export_fs, modulestore, course_id, course_location, category_type, dirname, file_suffix=''):
    query_loc = Location('i4x', course_location.org, course_location.course, category_type, None)
    items = modulestore.get_items(query_loc, course_id)

    if len(items) > 0:
        item_dir = export_fs.makeopendir(dirname)
        for item in items:
            with item_dir.open(item.location.name + file_suffix, 'w') as item_file:
                item_file.write(item.data.encode('utf8'))
