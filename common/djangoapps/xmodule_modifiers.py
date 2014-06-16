"""
Functions that can are used to modify XBlock fragments for use in the LMS and Studio
"""

import datetime
import json
import logging
import static_replace

from django.conf import settings
from django.utils.timezone import UTC
from edxmako.shortcuts import render_to_string
from xblock.exceptions import InvalidScopeError
from xblock.fragment import Fragment

from xmodule.seq_module import SequenceModule
from xmodule.vertical_module import VerticalModule
from xmodule.x_module import shim_xmodule_js, XModuleDescriptor, XModule, PREVIEW_VIEWS, STUDIO_VIEW
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


def wrap_fragment(fragment, new_content):
    """
    Returns a new Fragment that has `new_content` and all
    as its content, and all of the resources from fragment
    """
    wrapper_frag = Fragment(content=new_content)
    wrapper_frag.add_frag_resources(fragment)
    return wrapper_frag


def wrap_xblock(runtime_class, block, view, frag, context, usage_id_serializer, display_name_only=False, extra_data=None):  # pylint: disable=unused-argument
    """
    Wraps the results of rendering an XBlock view in a standard <section> with identifying
    data so that the appropriate javascript module can be loaded onto it.

    :param runtime_class: The name of the javascript runtime class to use to load this block
    :param block: An XBlock (that may be an XModule or XModuleDescriptor)
    :param view: The name of the view that rendered the fragment being wrapped
    :param frag: The :class:`Fragment` to be wrapped
    :param context: The context passed to the view being rendered
    :param usage_id_serializer: A function to serialize the block's usage_id for use by the
        front-end Javascript Runtime.
    :param display_name_only: If true, don't render the fragment content at all.
        Instead, just render the `display_name` of `block`
    :param extra_data: A dictionary with extra data values to be set on the wrapper
    """
    if extra_data is None:
        extra_data = {}

    # If any mixins have been applied, then use the unmixed class
    class_name = getattr(block, 'unmixed_class', block.__class__).__name__

    data = {}
    data.update(extra_data)
    css_classes = ['xblock', 'xblock-' + view]

    if isinstance(block, (XModule, XModuleDescriptor)):
        if view in PREVIEW_VIEWS:
            # The block is acting as an XModule
            css_classes.append('xmodule_display')
        elif view == STUDIO_VIEW:
            # The block is acting as an XModuleDescriptor
            css_classes.append('xmodule_edit')

        css_classes.append('xmodule_' + class_name)
        data['type'] = block.js_module_name
        shim_xmodule_js(frag)

    if frag.js_init_fn:
        data['init'] = frag.js_init_fn
        data['runtime-class'] = runtime_class
        data['runtime-version'] = frag.js_init_version
        data['block-type'] = block.scope_ids.block_type
        data['usage-id'] = usage_id_serializer(block.scope_ids.usage_id)

    template_context = {
        'content': block.display_name if display_name_only else frag.content,
        'classes': css_classes,
        'display_name': block.display_name_with_default,
        'data_attributes': u' '.join(u'data-{}="{}"'.format(key, value)
                                     for key, value in data.iteritems()),
    }

    return wrap_fragment(frag, render_to_string('xblock_wrapper.html', template_context))


def replace_jump_to_id_urls(course_id, jump_to_id_base_url, block, view, frag, context):  # pylint: disable=unused-argument
    """
    This will replace a link between courseware in the format
    /jump_to/<id> with a URL for a page that will correctly redirect
    This is similar to replace_course_urls, but much more flexible and
    durable for Studio authored courses. See more comments in static_replace.replace_jump_to_urls

    course_id: The course_id in which this rewrite happens
    jump_to_id_base_url:
        A app-tier (e.g. LMS) absolute path to the base of the handler that will perform the
        redirect. e.g. /courses/<org>/<course>/<run>/jump_to_id. NOTE the <id> will be appended to
        the end of this URL at re-write time

    output: a new :class:`~xblock.fragment.Fragment` that modifies `frag` with
        content that has been update with /jump_to links replaced
    """
    return wrap_fragment(frag, static_replace.replace_jump_to_id_urls(frag.content, course_id, jump_to_id_base_url))


def replace_course_urls(course_id, block, view, frag, context):  # pylint: disable=unused-argument
    """
    Updates the supplied module with a new get_html function that wraps
    the old get_html function and substitutes urls of the form /course/...
    with urls that are /courses/<course_id>/...
    """
    return wrap_fragment(frag, static_replace.replace_course_urls(frag.content, course_id))


def replace_static_urls(data_dir, block, view, frag, context, course_id=None, static_asset_path=''):  # pylint: disable=unused-argument
    """
    Updates the supplied module with a new get_html function that wraps
    the old get_html function and substitutes urls of the form /static/...
    with urls that are /static/<prefix>/...
    """
    return wrap_fragment(frag, static_replace.replace_static_urls(
        frag.content,
        data_dir,
        course_id,
        static_asset_path=static_asset_path
    ))


def grade_histogram(module_id):
    '''
    Print out a histogram of grades on a given problem in staff member debug info.

    Warning: If a student has just looked at an xmodule and not attempted
    it, their grade is None. Since there will always be at least one such student
    this function almost always returns [].
    '''
    from django.db import connection
    cursor = connection.cursor()

    q = """SELECT courseware_studentmodule.grade,
                  COUNT(courseware_studentmodule.student_id)
    FROM courseware_studentmodule
    WHERE courseware_studentmodule.module_id=%s
    GROUP BY courseware_studentmodule.grade"""
    # Passing module_id this way prevents sql-injection.
    cursor.execute(q, [module_id.to_deprecated_string()])

    grades = list(cursor.fetchall())
    grades.sort(key=lambda x: x[0])  # Add ORDER BY to sql query?
    if len(grades) >= 1 and grades[0][0] is None:
        return []
    return grades


def add_staff_markup(user, has_instructor_access, block, view, frag, context):  # pylint: disable=unused-argument
    """
    Updates the supplied module with a new get_html function that wraps
    the output of the old get_html function with additional information
    for admin users only, including a histogram of student answers, the
    definition of the xmodule, and a link to view the module in Studio
    if it is a Studio edited, mongo stored course.

    Does nothing if module is a SequenceModule.
    """
    # TODO: make this more general, eg use an XModule attribute instead
    if isinstance(block, VerticalModule) and (not context or not context.get('child_of_vertical', False)):
        # check that the course is a mongo backed Studio course before doing work
        is_mongo_course = modulestore().get_modulestore_type(block.location.course_key) == ModuleStoreEnum.Type.mongo
        is_studio_course = block.course_edit_method == "Studio"

        if is_studio_course and is_mongo_course:
            # build edit link to unit in CMS. Can't use reverse here as lms doesn't load cms's urls.py
            edit_link = "//" + settings.CMS_BASE + '/container/' + unicode(block.location)

            # return edit link in rendered HTML for display
            return wrap_fragment(frag, render_to_string("edit_unit_link.html", {'frag_content': frag.content, 'edit_link': edit_link}))
        else:
            return frag

    if isinstance(block, SequenceModule):
        return frag

    block_id = block.location
    if block.has_score and settings.FEATURES.get('DISPLAY_HISTOGRAMS_TO_STAFF'):
        histogram = grade_histogram(block_id)
        render_histogram = len(histogram) > 0
    else:
        histogram = None
        render_histogram = False

    if settings.FEATURES.get('ENABLE_LMS_MIGRATION') and hasattr(block.runtime, 'filestore'):
        [filepath, filename] = getattr(block, 'xml_attributes', {}).get('filename', ['', None])
        osfs = block.runtime.filestore
        if filename is not None and osfs.exists(filename):
            # if original, unmangled filename exists then use it (github
            # doesn't like symlinks)
            filepath = filename
        data_dir = block.static_asset_path or osfs.root_path.rsplit('/')[-1]
        giturl = block.giturl or 'https://github.com/MITx'
        edit_link = "%s/%s/tree/master/%s" % (giturl, data_dir, filepath)
    else:
        edit_link = False
        # Need to define all the variables that are about to be used
        giturl = ""
        data_dir = ""

    source_file = block.source_file  # source used to generate the problem XML, eg latex or word

    # useful to indicate to staff if problem has been released or not
    # TODO (ichuang): use _has_access_descriptor.can_load in lms.courseware.access, instead of now>mstart comparison here
    now = datetime.datetime.now(UTC())
    is_released = "unknown"
    mstart = block.start

    if mstart is not None:
        is_released = "<font color='red'>Yes!</font>" if (now > mstart) else "<font color='green'>Not yet</font>"

    field_contents = []
    for name, field in block.fields.items():
        try:
            field_contents.append((name, field.read_from(block)))
        except InvalidScopeError:
            log.warning("Unable to read field in Staff Debug information", exc_info=True)
            field_contents.append((name, "WARNING: Unable to read field"))

    staff_context = {'fields': field_contents,
                     'xml_attributes': getattr(block, 'xml_attributes', {}),
                     'location': block.location,
                     'xqa_key': block.xqa_key,
                     'source_file': source_file,
                     'source_url': '%s/%s/tree/master/%s' % (giturl, data_dir, source_file),
                     'category': str(block.__class__.__name__),
                     # Template uses element_id in js function names, so can't allow dashes
                     'element_id': block.location.html_id().replace('-', '_'),
                     'edit_link': edit_link,
                     'user': user,
                     'xqa_server': settings.FEATURES.get('USE_XQA_SERVER', 'http://xqa:server@content-qa.mitx.mit.edu/xqa'),
                     'histogram': json.dumps(histogram),
                     'render_histogram': render_histogram,
                     'block_content': frag.content,
                     'is_released': is_released,
                     'has_instructor_access': has_instructor_access,
                     }
    return wrap_fragment(frag, render_to_string("staff_problem_info.html", staff_context))
