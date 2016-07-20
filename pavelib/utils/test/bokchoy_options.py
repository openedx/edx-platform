from optparse import make_option
import os


BOKCHOY_OPTS = [
    ('test-spec=', 't', 'Specific test to run'),
    ('fasttest', 'a', 'Skip some setup'),
    ('skip-clean', 'C', 'Skip cleaning repository before running tests'),
    ('serversonly', 'r', 'Prepare suite and leave servers running'),
    ('testsonly', 'o', 'Assume servers are running and execute tests only'),
    make_option("-s", "--default-store", default=os.environ.get('DEFAULT_STORE', 'split'), help='Default modulestore'),
    ('test-dir=', 'd', 'Directory for finding tests (relative to common/test/acceptance)'),
    ('imports-dir=', 'i', 'Directory containing (un-archived) courses to be imported'),
    ('num-processes=', 'n', 'Number of test threads (for multiprocessing)'),
    ('verify-xss', 'x', 'Run XSS vulnerability tests'),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity"),
    make_option("--skip-firefox-version-validation", action='store_false', dest="validate_firefox_version"),
    make_option("--save-screenshots", action='store_true', dest="save_screenshots"),
    make_option("--default_store", default=os.environ.get('DEFAULT_STORE', 'split'), help='deprecated in favor of default-store'),
    ('extra_args=', 'e', 'deprecated, pass extra options directly in the paver commandline'),
    ('imports_dir=', None, 'deprecated in favor of imports-dir'),
    ('num_processes=', None, 'deprecated in favor of num-processes'),
    ('skip_clean', None, 'deprecated in favor of skip-clean'),
    ('test_dir=', None, 'deprecated in favor of test-dir'),
    ('test_spec=', None, 'Specific test to run'),
    ('verify_xss', None, 'deprecated in favor of verify-xss'),
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


def parse_bokchoy_opts(options, passthrough_options=None):
    """
    Parses bok choy options.

    Returns: dict of options.
    """
    if passthrough_options is None:
        passthrough_options = []

    return {
        'test_spec': getattr(options, 'test_spec', None),
        'fasttest': getattr(options, 'fasttest', False),
        'num_processes': int(getattr(options, 'num_processes', 1)),
        'verify_xss': getattr(options, 'verify_xss', os.environ.get('VERIFY_XSS', False)),
        'serversonly': getattr(options, 'serversonly', False),
        'testsonly': getattr(options, 'testsonly', False),
        'default_store': getattr(options, 'default_store', os.environ.get('DEFAULT_STORE', 'split')),
        'verbosity': getattr(options, 'verbosity', 2),
        'extra_args': getattr(options, 'extra_args', ''),
        'pdb': getattr(options, 'pdb', False),
        'test_dir': getattr(options, 'test_dir', 'tests'),
        'imports_dir': getattr(options, 'imports_dir', None),
        'save_screenshots': getattr(options, 'save_screenshots', False),
        'passthrough_options': passthrough_options,
        'report_dir': getattr(options, 'report_dir', Env.BOK_CHOY_REPORT_DIR),
    }
