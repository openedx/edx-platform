"""
Definitions of all options used by the various bok_choy tasks.
"""

from optparse import make_option
import os

from pavelib.utils.envs import Env


BOKCHOY_IMPORTS_DIR = ('imports-dir=', 'i', 'Directory containing (un-archived) courses to be imported')
BOKCHOY_IMPORTS_DIR_DEPR = ('imports_dir=', None, 'deprecated in favor of imports-dir')
BOKCHOY_DEFAULT_STORE = make_option(
    "-s", "--default-store",
    default=os.environ.get('DEFAULT_STORE', 'split'),
    help='Default modulestore'
)
BOKCHOY_DEFAULT_STORE_DEPR = make_option(
    "--default_store",
    default=os.environ.get('DEFAULT_STORE', 'split'),
    help='deprecated in favor of default-store'
)
BOKCHOY_FASTTEST = make_option('-a', '--fasttest', action='store_true', help='Skip some setup')
BOKCHOY_COVERAGERC = make_option('--coveragerc', help='coveragerc file to use during this test')

BOKCHOY_OPTS = [
    ('test-spec=', 't', 'Specific test to run'),
    BOKCHOY_FASTTEST,
    ('skip-clean', 'C', 'Skip cleaning repository before running tests'),
    make_option('-r', '--serversonly', action='store_true', help='Prepare suite and leave servers running'),
    make_option('-o', '--testsonly', action='store_true', help='Assume servers are running and execute tests only'),
    BOKCHOY_DEFAULT_STORE,
    make_option(
        '-d', '--test-dir',
        default='tests',
        help='Directory for finding tests (relative to openedx/tests/acceptance)'
    ),
    BOKCHOY_IMPORTS_DIR,
    make_option('-n', '--num-processes', type='int', help='Number of test threads (for multiprocessing)'),
    make_option(
        '-x', '--verify-xss',
        action='store_true',
        default=os.environ.get('VERIFY_XSS', False),
        help='Run XSS vulnerability tests'
    ),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity"),
    make_option("--skip-firefox-version-validation", action='store_false', dest="validate_firefox_version"),
    make_option("--save-screenshots", action='store_true', dest="save_screenshots"),
    make_option("--report-dir", default=Env.BOK_CHOY_REPORT_DIR, help="Directory to store reports in"),

    BOKCHOY_DEFAULT_STORE_DEPR,
    make_option(
        '-e', '--extra_args',
        default='',
        help='deprecated, pass extra options directly in the paver commandline'
    ),
    BOKCHOY_IMPORTS_DIR_DEPR,
    make_option('--num_processes', type='int', help='deprecated in favor of num-processes'),
    ('skip_clean', None, 'deprecated in favor of skip-clean'),
    make_option('--test_dir', default='tests', help='deprecated in favor of test-dir'),
    ('test_spec=', None, 'Specific test to run'),
    make_option(
        '--verify_xss',
        action='store_true',
        default=os.environ.get('VERIFY_XSS', False),
        help='deprecated in favor of verify-xss'
    ),
    make_option(
        "--skip_firefox_version_validation",
        action='store_false',
        dest="validate_firefox_version",
        help="deprecated in favor of --skip-firefox-version-validation"
    ),
    make_option(
        "--save_screenshots",
        action='store_true',
        dest="save_screenshots",
        help="deprecated in favor of save-screenshots"
    ),
]

PA11Y_HTML = ('with-html', 'w', 'Include html reports')
PA11Y_COURSE_KEY = make_option('--course-key', help='Course key for test course')
PA11Y_FETCH_COURSE = make_option(
    "--fetch-course",
    action="store_true",
    dest="should_fetch_course",
    help='Course key for test course',
)
