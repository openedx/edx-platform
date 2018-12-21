"""
TestSuite class and subclasses
"""
from .suite import TestSuite
from .pytest_suite import PytestSuite, SystemTestSuite, LibTestSuite
from .python_suite import PythonTestSuite
from .js_suite import JsTestSuite, JestSnapshotTestSuite
from .acceptance_suite import AcceptanceTestSuite
from .bokchoy_suite import BokChoyTestSuite, Pa11yCrawler
