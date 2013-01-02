import re
import json
import logging
import time

from django.conf import settings
from functools import wraps
from static_replace import replace_urls
from mitxmako.shortcuts import render_to_string
from xmodule.seq_module import SequenceModule
from xmodule.vertical_module import VerticalModule

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
            'display_name': module.lms.display_name,
            'class_': module.__class__.__name__,
            'module_name': module.js_module_name
        })

        return render_to_string(template, context)
    return _get_html


def replace_course_urls(get_html, course_id):
    """
    Updates the supplied module with a new get_html function that wraps
    the old get_html function and substitutes urls of the form /course/...
    with urls that are /courses/<course_id>/...
    """
    @wraps(get_html)
    def _get_html():
        return replace_urls(get_html(), staticfiles_prefix='/courses/'+course_id, replace_prefix='/course/')
    return _get_html

def replace_static_urls(get_html, prefix, course_namespace=None):
    """
    Updates the supplied module with a new get_html function that wraps
    the old get_html function and substitutes urls of the form /static/...
    with urls that are /static/<prefix>/...
    """

    @wraps(get_html)
    def _get_html():
        return replace_urls(get_html(), staticfiles_prefix=prefix, course_namespace = course_namespace)
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
    grades.sort(key=lambda x: x[0])          # Add ORDER BY to sql query?
    if len(grades) >= 1 and grades[0][0] is None:
        return []
    return grades


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

        if type(module) in [SequenceModule, VerticalModule]:	# TODO: make this more general, eg use an XModule attribute instead
            return get_html()

        module_id = module.id
        histogram = grade_histogram(module_id)
        render_histogram = len(histogram) > 0

        source_file = module.lms.source_file  # source used to generate the problem XML, eg latex or word

        # useful to indicate to staff if problem has been released or not
        # TODO (ichuang): use _has_access_descriptor.can_load in lms.courseware.access, instead of now>mstart comparison here
        now = time.gmtime()
        is_released = "unknown"
        mstart = getattr(module.descriptor.lms,'start')
        if mstart is not None:
            is_released = "<font color='red'>Yes!</font>" if (now > mstart) else "<font color='green'>Not yet</font>"

        staff_context = {'fields': [(field.name, getattr(module, field.name)) for field in module.fields],
                         'lms_fields': [(field.name, getattr(module.lms, field.name)) for field in module.lms.fields],
                         'location': module.location,
                         'xqa_key': module.lms.xqa_key,
                         'source_file' : source_file,
                         'category': str(module.__class__.__name__),
                         # Template uses element_id in js function names, so can't allow dashes
                         'element_id': module.location.html_id().replace('-','_'),
                         'user': user,
                         'xqa_server' : settings.MITX_FEATURES.get('USE_XQA_SERVER','http://xqa:server@content-qa.mitx.mit.edu/xqa'),
                         'histogram': json.dumps(histogram),
                         'render_histogram': render_histogram,
                         'module_content': get_html(),
                         'is_released': is_released,
                         }
        return render_to_string("staff_problem_info.html", staff_context)

    return _get_html

