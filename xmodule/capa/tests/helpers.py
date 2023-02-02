"""Tools for helping with testing capa."""


import gettext
import io
import os
import os.path
import xml.sax.saxutils as saxutils

import fs.osfs
import six
from mako.lookup import TemplateLookup
from mock import MagicMock, Mock
from path import Path

from xmodule.capa.capa_problem import LoncapaProblem, LoncapaSystem
from xmodule.capa.inputtypes import Status

TEST_DIR = os.path.dirname(os.path.realpath(__file__))


def get_template(template_name):
    """
    Return template for a capa inputtype.
    """
    return TemplateLookup(
        directories=[Path(__file__).dirname().dirname() / 'templates'],
        default_filters=['decode.utf8']
    ).get_template(template_name)


def capa_render_template(template, context):
    """
    Render template for a capa inputtype.
    """
    return get_template(template).render_unicode(**context)


def tst_render_template(template, context):  # pylint: disable=unused-argument
    """
    A test version of render to template.  Renders to the repr of the context, completely ignoring
    the template name.  To make the output valid xml, quotes the content, and wraps it in a <div>
    """
    return '<div>{0}</div>'.format(saxutils.escape(repr(context)))


class StubXQueueService:
    """
    Stubs out the XQueueService for Capa problem tests.
    """
    def __init__(self):
        self.interface = MagicMock()
        self.interface.send_to_queue.return_value = (0, 'Success!')
        self.default_queuename = 'testqueue'
        self.waittime = 10

    def construct_callback(self, dispatch='score_update'):
        """A callback url method to use in tests."""
        return dispatch


def test_capa_system(render_template=None):
    """
    Construct a mock LoncapaSystem instance.

    """
    the_system = Mock(
        spec=LoncapaSystem,
        ajax_url='/dummy-ajax-url',
        anonymous_student_id='student',
        cache=None,
        can_execute_unsafe_code=lambda: False,
        get_python_lib_zip=lambda: None,
        DEBUG=True,
        i18n=gettext.NullTranslations(),
        render_template=render_template or tst_render_template,
        resources_fs=fs.osfs.OSFS(os.path.join(TEST_DIR, "test_files")),
        seed=0,
        STATIC_URL='/dummy-static/',
        STATUS_CLASS=Status,
        xqueue=StubXQueueService(),
    )
    return the_system


def mock_capa_block():
    """
    capa response types needs just two things from the capa_block: location and publish.
    """
    def mock_location_text(self):  # lint-amnesty, pylint: disable=unused-argument
        """
        Mock implementation of __unicode__ or __str__ for the block's location.
        """
        return 'i4x://Foo/bar/mock/abc'

    capa_block = Mock()
    if six.PY2:
        capa_block.location.__unicode__ = mock_location_text
    else:
        capa_block.location.__str__ = mock_location_text
    # The following comes into existence by virtue of being called
    # capa_block.runtime.publish
    return capa_block


def new_loncapa_problem(xml, problem_id='1', capa_system=None, seed=723, use_capa_render_template=False):
    """Construct a `LoncapaProblem` suitable for unit tests."""
    render_template = capa_render_template if use_capa_render_template else None
    return LoncapaProblem(xml, id=problem_id, seed=seed, capa_system=capa_system or test_capa_system(render_template),
                          capa_block=mock_capa_block())


def load_fixture(relpath):
    """
    Return a `unicode` object representing the contents
    of the fixture file at the given path within a test_files directory
    in the same directory as the test file.
    """
    abspath = os.path.join(os.path.dirname(__file__), 'test_files', relpath)
    with io.open(abspath, encoding="utf-8") as fixture_file:
        contents = fixture_file.read()
        return contents
