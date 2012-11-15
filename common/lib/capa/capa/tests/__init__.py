import fs
import fs.osfs
import os

from mock import Mock

import xml.sax.saxutils as saxutils

TEST_DIR = os.path.dirname(os.path.realpath(__file__))

def tst_render_template(template, context):
    """
    A test version of render to template.  Renders to the repr of the context, completely ignoring
    the template name.  To make the output valid xml, quotes the content, and wraps it in a <div>
    """
    return '<div>{0}</div>'.format(saxutils.escape(repr(context)))


test_system = Mock(
    ajax_url='courses/course_id/modx/a_location',
    track_function=Mock(),
    get_module=Mock(),
    render_template=tst_render_template,
    replace_urls=Mock(),
    user=Mock(),
    filestore=fs.osfs.OSFS(os.path.join(TEST_DIR, "test_files")),
    debug=True,
    xqueue={'interface':None, 'callback_url':'/', 'default_queuename': 'testqueue', 'waittime': 10},
    node_path=os.environ.get("NODE_PATH", "/usr/local/lib/node_modules"),
    anonymous_student_id = 'student'
)
