import json
from django.conf import settings
from functools import wraps
from static_replace import replace_urls
from mitxmako.shortcuts import render_to_string


def wrap_xmodule(get_html, module, template):
    """
    Wraps the results of get_html in a standard <section> with identifying
    data so that the appropriate javascript module can be loaded onto it.

    get_html: An XModule.get_html method or an XModuleDescriptor.get_html method
    module: An XModule
    template: A template that takes the variables:
        content: the results of get_html,
        class_: the module class name
        module_name: the js_module_name of the module
    """

    @wraps(get_html)
    def _get_html():
        return render_to_string(template, {
            'content': get_html(),
            'class_': module.__class__.__name__,
            'module_name': module.js_module_name
        })
    return _get_html


def replace_static_urls(get_html, prefix):
    """
    Updates the supplied module with a new get_html function that wraps
    the old get_html function and substitutes urls of the form /static/...
    with urls that are /static/<prefix>/...
    """

    @wraps(get_html)
    def _get_html():
        return replace_urls(get_html(), staticfiles_prefix=prefix)
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
    if len(grades) == 1 and grades[0][0] is None:
        return []
    return grades


def add_histogram(get_html, module):
    """
    Updates the supplied module with a new get_html function that wraps
    the output of the old get_html function with additional information
    for admin users only, including a histogram of student answers and the
    definition of the xmodule
    """
    @wraps(get_html)
    def _get_html():
        module_id = module.id
        histogram = grade_histogram(module_id)
        render_histogram = len(histogram) > 0

        # TODO: fixme - no filename in module.xml in general (this code block
        # for edx4edx) the following if block is for summer 2012 edX course
        # development; it will change when the CMS comes online
        if settings.MITX_FEATURES.get('DISPLAY_EDIT_LINK') and settings.DEBUG and module_xml.get('filename') is not None:
            coursename = multicourse_settings.get_coursename_from_request(request)
            github_url = multicourse_settings.get_course_github_url(coursename)
            fn = module_xml.get('filename')
            if module_xml.tag=='problem': fn = 'problems/' + fn	# grrr
            edit_link = (github_url + '/tree/master/' + fn) if github_url is not None else None
            if module_xml.tag=='problem': edit_link += '.xml'	# grrr
        else:
            edit_link = False

        staff_context = {'definition': json.dumps(module.definition, indent=4),
                         'metadata': json.dumps(module.metadata, indent=4),
                         'element_id': module.location.html_id(),
                         'edit_link': edit_link,
                         'histogram': json.dumps(histogram),
                         'render_histogram': render_histogram,
                         'module_content': get_html()}
        return render_to_string("staff_problem_info.html", staff_context)

    return _get_html
