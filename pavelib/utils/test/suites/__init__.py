"""
TestSuite class and subclasses
"""
from .suite import TestSuite
from .pytest_suite import PytestSuite, SystemTestSuite, LibTestSuite, default_system_test_dirs
from .python_suite import PythonTestSuite
from .js_suite import JsTestSuite
from .acceptance_suite import AcceptanceTestSuite
from .bokchoy_suite import BokChoyTestSuite, Pa11yCrawler
