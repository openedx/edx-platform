"""
Default unit test configuration and fixtures.
"""

from __future__ import absolute_import, unicode_literals


# skip everything except pavelib "test_extract_and_generate"
collect_ignore = [
    'lms/',
    'cms/',
    'common/',
    'openedx/',
    'pavelib/paver_tests/test_eslint.py',
    'pavelib/paver_tests/test_prereqs.py',
    'pavelib/paver_tests/test_paver_bok_choy_cmds.py',
    'pavelib/paver_tests/test_xsscommitlint.py',
    'pavelib/paver_tests/test_xsslint.py',
    'pavelib/paver_tests/test_paver_quality.py',
    'pavelib/paver_tests/test_timer.py',
    'pavelib/paver_tests/test_js_test.py',
    'pavelib/paver_tests/test_i18n.py',
    'pavelib/paver_tests/test_stylelint.py',
    'pavelib/paver_tests/test_utils.py',
    'pavelib/paver_tests/test_servers.py',
    'pavelib/paver_tests/test_assets.py',
    'pavelib/paver_tests/test_paver_get_quality_reports.py',
]


# Import hooks and fixture overrides from the cms package to
# avoid duplicating the implementation

from cms.conftest import _django_clear_site_cache, pytest_configure  # pylint: disable=unused-import
