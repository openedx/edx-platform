import fs
import fs.osfs
import os

from mock import Mock

TEST_DIR = os.path.dirname(os.path.realpath(__file__))

test_system = Mock(
    ajax_url='courses/course_id/modx/a_location',
    track_function=Mock(),
    get_module=Mock(),
    render_template=Mock(),
    replace_urls=Mock(),
    user=Mock(),
    filestore=fs.osfs.OSFS(os.path.join(TEST_DIR, "test_files")),
    debug=True,
    xqueue={'interface':None, 'callback_url':'/', 'default_queuename': 'testqueue', 'waittime': 10},
    node_path=os.environ.get("NODE_PATH", "/usr/local/lib/node_modules"),
    anonymous_student_id = 'student'
)
