"""
Tests for the Tahoe-specific modifications of `xmodule/modulestore/django.py`.
"""

from xmodule.modulestore.django import ModuleI18nService


def test_prevent_recursion_error_in_module_i18n_service():
    """
    Ensure that ModuleI18nService has no fallback to avoid RecursionError in some XBlocks.

    See RED-2263 and https://github.com/appsembler/edx-platform/pull/953 for more details.
    """
    assert '_fallback' in ModuleI18nService.__dict__, 'ModuleI18nService should have explicit fallback'
    assert ModuleI18nService._fallback is None, 'Fix RecursionError in certain XBlocks'
