import json
import logging
import static_replace

from django.conf import settings
from functools import wraps
from mitxmako.shortcuts import render_to_string
from xmodule.seq_module import SequenceModule
from xmodule.vertical_module import VerticalModule
import datetime
from django.utils.timezone import UTC

log = logging.getLogger("mitx.xmodule_modifiers")


def wrap_xmodule(get_html, module, template, context=None):
    """
    Wraps the results of get_html in a standard <section> with identifying
    data so that the appropriate javascript module can be loaded onto it.

    get_html: An XModule.get_html method or an XModuleDescriptor.get_html method
    module: An XModule
    template: A template that takes the variables:
        content: the results of get_html,
        display_name: the display name of the xmodule, if available (None otherwise)
        class_: the module class name
        module_name: the js_module_name of the module
    """
    if context is None:
        context = {}

    @wraps(get_html)
    def _get_html():
        context.update({
            'content': get_html(),
            'display_name': module.display_name,
            'class_': module.__class__.__name__,
            'module_name': module.js_module_name
        })

        return render_to_string(template, context)
    return _get_html


def replace_jump_to_id_urls(get_html, course_id, jump_to_id_base_url):
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

    output: a wrapped get_html() function pointer, which, when called, will apply the
        rewrite rules
    """
    @wraps(get_html)
    def _get_html():
        return static_replace.replace_jump_to_id_urls(get_html(), course_id, jump_to_id_base_url)
    return _get_html


def replace_course_urls(get_html, course_id):
    """
    Updates the supplied module with a new get_html function that wraps
    the old get_html function and substitutes urls of the form /course/...
    with urls that are /courses/<course_id>/...
    """
    @wraps(get_html)
    def _get_html():
        return static_replace.replace_course_urls(get_html(), course_id)
    return _get_html


def replace_static_urls(get_html, data_dir, course_id=None):
    """
    Updates the supplied module with a new get_html function that wraps
    the old get_html function and substitutes urls of the form /static/...
    with urls that are /static/<prefix>/...
    """

    @wraps(get_html)
    def _get_html():
        return static_replace.replace_static_urls(get_html(), data_dir, course_id)
    return _get_html


def grade_histogram(module_id):
    ''' Print out a histogram of grades on a given problem.
        Part of staff member debug info.
    '''
    from django.db import connection
    cursor = connection.cursor()

    q = """SELECT courseware_studentmodule.grade,
                  COUNT(courseware_studentmodule.student_id)
    FROM courseware_studentmodule
    WHERE courseware_studentmodule.module_id=%s
    GROUP BY courseware_studentmodule.grade"""
    # Passing module_id this way prevents sql-injection.
    cursor.execute(q, [module_id])

    grades = list(cursor.fetchall())
    grades.sort(key=lambda x: x[0])  # Add ORDER BY to sql query?
    if len(grades) >= 1 and grades[0][0] is None:
        return []
    return grades


def save_module(get_html, module):
    """
    Updates the given get_html function for the given module to save the fields
    after rendering.
    """
    @wraps(get_html)
    def _get_html():
        """Cache the rendered output, save, then return the output."""
        rendered_html = get_html()
        module.save()
        return rendered_html

    return _get_html


def add_histogram(get_html, module, user):
    """
    Updates the supplied module with a new get_html function that wraps
    the output of the old get_html function with additional information
    for admin users only, including a histogram of student answers and the
    definition of the xmodule

    Does nothing if module is a SequenceModule or a VerticalModule.
    """
    @wraps(get_html)
    def _get_html():

        if type(module) in [SequenceModule, VerticalModule]:  # TODO: make this more general, eg use an XModule attribute instead
            return get_html()

        module_id = module.id
        if module.descriptor.has_score:
            histogram = grade_histogram(module_id)
            render_histogram = len(histogram) > 0
        else:
            histogram = None
            render_histogram = False

        if settings.MITX_FEATURES.get('ENABLE_LMS_MIGRATION'):
            [filepath, filename] = getattr(module.descriptor, 'xml_attributes', {}).get('filename', ['', None])
            osfs = module.system.filestore
            if filename is not None and osfs.exists(filename):
                # if original, unmangled filename exists then use it (github
                # doesn't like symlinks)
                filepath = filename
            data_dir = osfs.root_path.rsplit('/')[-1]
            giturl = module.lms.giturl or 'https://github.com/MITx'
            edit_link = "%s/%s/tree/master/%s" % (giturl, data_dir, filepath)
        else:
            edit_link = False
            # Need to define all the variables that are about to be used
            giturl = ""
            data_dir = ""

        source_file = module.lms.source_file  # source used to generate the problem XML, eg latex or word

        # useful to indicate to staff if problem has been released or not
        # TODO (ichuang): use _has_access_descriptor.can_load in lms.courseware.access, instead of now>mstart comparison here
        now = datetime.datetime.now(UTC())
        is_released = "unknown"
        mstart = module.descriptor.lms.start

        if mstart is not None:
            is_released = "<font color='red'>Yes!</font>" if (now > mstart) else "<font color='green'>Not yet</font>"

        staff_context = {'fields': [(field.name, getattr(module, field.name)) for field in module.fields],
                         'lms_fields': [(field.name, getattr(module.lms, field.name)) for field in module.lms.fields],
                         'xml_attributes' : getattr(module.descriptor, 'xml_attributes', {}),
                         'location': module.location,
                         'xqa_key': module.lms.xqa_key,
                         'source_file': source_file,
                         'source_url': '%s/%s/tree/master/%s' % (giturl, data_dir, source_file),
                         'category': str(module.__class__.__name__),
                         # Template uses element_id in js function names, so can't allow dashes
                         'element_id': module.location.html_id().replace('-', '_'),
                         'edit_link': edit_link,
                         'user': user,
                         'xqa_server': settings.MITX_FEATURES.get('USE_XQA_SERVER', 'http://xqa:server@content-qa.mitx.mit.edu/xqa'),
                         'histogram': json.dumps(histogram),
                         'render_histogram': render_histogram,
                         'module_content': get_html(),
                         'is_released': is_released,
                         }
        return render_to_string("staff_problem_info.html", staff_context)

    return _get_html
