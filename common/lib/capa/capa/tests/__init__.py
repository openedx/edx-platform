"""Tools for helping with testing capa."""

import os
import os.path

import fs.osfs

from capa.capa_problem import LoncapaProblem, LoncapaSystem
from mock import Mock, MagicMock

import xml.sax.saxutils as saxutils

TEST_DIR = os.path.dirname(os.path.realpath(__file__))


def tst_render_template(template, context):
    """
    A test version of render to template.  Renders to the repr of the context, completely ignoring
    the template name.  To make the output valid xml, quotes the content, and wraps it in a <div>
    """
    return '<div>{0}</div>'.format(saxutils.escape(repr(context)))


def calledback_url(dispatch='score_update'):
    return dispatch

xqueue_interface = MagicMock()
xqueue_interface.send_to_queue.return_value = (0, 'Success!')


def test_capa_system():
    """
    Construct a mock LoncapaSystem instance.

    """
    the_system = Mock(
        spec=LoncapaSystem,
        ajax_url='/dummy-ajax-url',
        anonymous_student_id='student',
        cache=None,
        can_execute_unsafe_code=lambda: False,
        DEBUG=True,
        filestore=fs.osfs.OSFS(os.path.join(TEST_DIR, "test_files")),
        node_path=os.environ.get("NODE_PATH", "/usr/local/lib/node_modules"),
        render_template=tst_render_template,
        seed=0,
        STATIC_URL='/dummy-static/',
        xqueue={'interface': xqueue_interface, 'construct_callback': calledback_url, 'default_queuename': 'testqueue', 'waittime': 10},
    )
    return the_system


def new_loncapa_problem(xml, capa_system=None):
    """Construct a `LoncapaProblem` suitable for unit tests."""
    return LoncapaProblem(xml, id='1', seed=723, capa_system=capa_system or test_capa_system())
