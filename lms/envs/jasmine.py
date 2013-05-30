"""
This configuration is used for running jasmine tests
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .test import *
from logsettings import get_logger_config

ENABLE_JASMINE = True
DEBUG = True

LOGGING = get_logger_config(TEST_ROOT / "log",
                            logging_env="dev",
                            tracking_filename="tracking.log",
                            dev_env=True,
                            debug=True,
                            local_loglevel='ERROR',
                            console_loglevel='ERROR')

PIPELINE_JS['js-test-source'] = {
    'source_filenames': sum([
        pipeline_group['source_filenames']
        for group_name, pipeline_group
        in sorted(PIPELINE_JS.items(), key=lambda item: item[1].get('test_order', 1e100))
        if group_name != 'spec'
    ], []),
    'output_filename': 'js/lms-test-source.js'
}

PIPELINE_JS['spec'] = {
    'source_filenames': sorted(rooted_glob(PROJECT_ROOT / 'static/', 'coffee/spec/**/*.js')),
    'output_filename': 'js/lms-spec.js'
}

JASMINE_TEST_DIRECTORY = PROJECT_ROOT + '/static/coffee'
JASMINE_REPORT_DIR = os.environ.get('JASMINE_REPORT_DIR', 'reports/lms/jasmine')

TEMPLATE_CONTEXT_PROCESSORS += ('settings_context_processor.context_processors.settings',)
TEMPLATE_VISIBLE_SETTINGS = ('JASMINE_REPORT_DIR', )

STATICFILES_DIRS.append(REPO_ROOT/'node_modules/phantom-jasmine/lib')
STATICFILES_DIRS.append(REPO_ROOT/'node_modules/jasmine-reporters/src')

INSTALLED_APPS += ('django_jasmine', 'settings_context_processor')
