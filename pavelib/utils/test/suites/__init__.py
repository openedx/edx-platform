"""
TestSuite class and subclasses
"""
from .js_suite import JestSnapshotTestSuite, JsTestSuite
from .pytest_suite import LibTestSuite, PytestSuite, SystemTestSuite
from .python_suite import PythonTestSuite
from .suite import TestSuite
