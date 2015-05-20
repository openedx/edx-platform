"""
TestSuite class and subclasses
"""
from .suite import TestSuite
from .nose_suite import NoseTestSuite, SystemTestSuite, LibTestSuite
from .python_suite import PythonTestSuite
from .js_suite import JsTestSuite
from .acceptance_suite import AcceptanceTestSuite
from .bokchoy_suite import BokChoyTestSuite
