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


def replace_course_urls(get_html, course_id, module):
    """
    Updates the supplied module with a new get_html function that wraps
    the old get_html function and substitutes urls of the form /course/...
    with urls that are /courses/<course_id>/...
    """
    @wraps(get_html)
    def _get_html():
        return replace_urls(get_html(), staticfiles_prefix='/courses/'+course_id, replace_prefix='/course/')
    return _get_html

def replace_static_urls(get_html, prefix, module):
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

        # TODO (ichuang): Remove after fall 2012 LMS migration done
        if settings.MITX_FEATURES.get('ENABLE_LMS_MIGRATION'):
            [filepath, filename] = module.definition.get('filename', ['', None])
            osfs = module.system.filestore
            if filename is not None and osfs.exists(filename):
                # if original, unmangled filename exists then use it (github
                # doesn't like symlinks)
                filepath = filename
            data_dir = osfs.root_path.rsplit('/')[-1]
            giturl = module.metadata.get('giturl','https://github.com/MITx')
            edit_link = "%s/%s/tree/master/%s" % (giturl,data_dir,filepath)
        else:
            edit_link = False
            # Need to define all the variables that are about to be used
            giturl = ""
            data_dir = ""
        source_file = module.metadata.get('source_file','')	# source used to generate the problem XML, eg latex or word

        # useful to indicate to staff if problem has been released or not
        now = time.gmtime()
        is_released = "unknown"
        if hasattr(module,'start'):
            if module.start is not None:
                is_released = "<font color='red'>Yes!</font>" if (now > module.start) else "<font color='green'>Not yet</font>"
        
        staff_context = {'definition': module.definition.get('data'),
                         'metadata': json.dumps(module.metadata, indent=4),
                         'location': module.location,
                         'xqa_key': module.metadata.get('xqa_key',''),
                         'source_file' : source_file,
                         'source_url': '%s/%s/tree/master/%s' % (giturl,data_dir,source_file),
                         'category': str(module.__class__.__name__),
                         'element_id': module.location.html_id().replace('-','_'),
                         'edit_link': edit_link,
                         'user': user,
                         'xqa_server' : settings.MITX_FEATURES.get('USE_XQA_SERVER','http://xqa:server@content-qa.mitx.mit.edu/xqa'),
                         'histogram': json.dumps(histogram),
                         'render_histogram': render_histogram,
                         'module_content': get_html(),
                         'is_released': is_released,
                         }
        return render_to_string("staff_problem_info.html", staff_context)

    return _get_html

