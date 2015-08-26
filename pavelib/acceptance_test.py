"""
Acceptance test tasks
"""
from paver.easy import task, cmdopts, needs
from pavelib.utils.test.suites import AcceptanceTestSuite
from optparse import make_option

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text  # pylint: disable-msg=invalid-name

__test__ = False  # do not collect


@task
@needs(
    'pavelib.prereqs.install_prereqs',
    'pavelib.utils.test.utils.clean_reports_dir',
)
@cmdopts([
    ("system=", "s", "System to act on"),
    ("default_store=", "m", "Default modulestore to use for course creation"),
    ("fasttest", "a", "Run without collectstatic"),
    ("extra_args=", "e", "adds as extra args to the test command"),
    make_option("--verbose", action="store_const", const=2, dest="verbosity"),
    make_option("-q", "--quiet", action="store_const", const=0, dest="verbosity"),
    make_option("-v", "--verbosity", action="count", dest="verbosity"),
    make_option("--pdb", action="store_true", help="Launches an interactive debugger upon error"),
])
def test_acceptance(options):
    """
    Run the acceptance tests for the either lms or cms
    """
    opts = {
        'fasttest': getattr(options, 'fasttest', False),
        'system': getattr(options, 'system', None),
        'default_store': getattr(options, 'default_store', None),
        'verbosity': getattr(options, 'verbosity', 3),
        'extra_args': getattr(options, 'extra_args', ''),
        'pdb': getattr(options, 'pdb', False),
    }

    if opts['system'] not in ['cms', 'lms']:
        msg = colorize(
            'red',
            'No system specified, running tests for both cms and lms.'
        )
        print(msg)
    if opts['default_store'] not in ['draft', 'split']:
        msg = colorize(
            'red',
            'No modulestore specified, running tests for both draft and split.'
        )
        print(msg)

    suite = AcceptanceTestSuite('{} acceptance'.format(opts['system']), **opts)
    suite.run()
