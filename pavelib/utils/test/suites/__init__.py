"""
TestSuite class and subclasses
"""
__all__ = ["TestSuite", "PythonTestSuite", "NoseTestSuite", "SystemTestSuite", "LibTestSuite", "JsTestSuite", "I18nTestSuite"]

from .suite import TestSuite
from .nose_suite import NoseTestSuite, SystemTestSuite, LibTestSuite
from .python_suite import PythonTestSuite
from .js_suite import JsTestSuite
from .i18n_suite import I18nTestSuite
