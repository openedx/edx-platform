"""
This configuration is used for running jasmine tests
"""

from .test import *
from logsettings import get_logger_config

ENABLE_JASMINE = True
DEBUG = True

LOGGING = get_logger_config(ENV_ROOT / "log",
                            logging_env="dev",
                            tracking_filename="tracking.log",
                            dev_env=True,
                            debug=True)

PIPELINE_JS['js-test-source'] = {
    'source_filenames': sum([
        pipeline_group['source_filenames']
        for pipeline_group
        in PIPELINE_JS.values()
    ], []),
    'output_filename': 'js/lms-test-source.js'
}

PIPELINE_JS['spec'] = {
    'source_filenames': sorted(rooted_glob(PROJECT_ROOT / 'static/', 'coffee/spec/**/*.coffee')),
    'output_filename': 'js/lms-spec.js'
}

STATICFILES_DIRS.append(COMMON_ROOT / 'test' / 'phantom-jasmine' / 'lib')
