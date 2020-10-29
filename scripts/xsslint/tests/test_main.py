# -*- coding: utf-8 -*-
"""
Tests for main.py
"""


import re
from six import StringIO
from unittest import TestCase

import mock

from xsslint.linters import JavaScriptLinter, MakoTemplateLinter, PythonLinter, UnderscoreTemplateLinter
from xsslint.main import _build_ruleset, _lint
from xsslint.reporting import SummaryResults


class TestXSSLinter(TestCase):
    """
    Test some top-level linter functions
    """

    def setUp(self):
        """
        Setup patches on linters for testing.
        """
        self.patch_is_valid_directory(MakoTemplateLinter)
        self.patch_is_valid_directory(JavaScriptLinter)
        self.patch_is_valid_directory(UnderscoreTemplateLinter)
        self.patch_is_valid_directory(PythonLinter)

        patcher = mock.patch('xsslint.main.is_skip_dir', return_value=False)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.out = StringIO()
        self.template_linters = self._build_linters()
        self.ruleset = _build_ruleset(self.template_linters)
        self.summary_results = SummaryResults(self.ruleset)

    def patch_is_valid_directory(self, linter_class):
        """
        Creates a mock patch for _is_valid_directory on a Linter to always
        return true. This avoids nested patch calls.

        Arguments:
            linter_class: The linter class to be patched
        """
        patcher = mock.patch.object(linter_class, '_is_valid_directory', return_value=True)
        patch_start = patcher.start()
        self.addCleanup(patcher.stop)
        return patch_start

    def _build_linters(self):
        underscore_linter = UnderscoreTemplateLinter()
        python_linter = PythonLinter()
        javascript_linter = JavaScriptLinter(underscore_linter=underscore_linter)
        mako_linter = MakoTemplateLinter(javascript_linter=javascript_linter, python_linter=python_linter)
        return [mako_linter, underscore_linter, javascript_linter, python_linter]

    def test_lint_defaults(self):
        """
        Tests the top-level linting with default options.
        """
        _lint(
            'scripts/xsslint/tests/templates',
            template_linters=self.template_linters,
            options={
                'list_files': False,
                'verbose': False,
                'rule_totals': False,
                'skip_dirs': ()
            },
            summary_results=self.summary_results,
            out=self.out,
        )

        output = self.out.getvalue()
        # Assert violation details are displayed.
        self.assertIsNotNone(re.search(r'test\.html.*{}'.format(self.ruleset.mako_missing_default.rule_id), output))
        self.assertIsNotNone(re.search(r'test\.js.*{}'.format(self.ruleset.javascript_concat_html.rule_id), output))
        self.assertIsNotNone(re.search(r'test\.js.*{}'.format(self.ruleset.underscore_not_escaped.rule_id), output))
        lines_with_rule = 0
        lines_without_rule = 0  # Output with verbose setting only.
        for underscore_match in re.finditer(r'test\.underscore:.*\n', output):
            if re.search(self.ruleset.underscore_not_escaped.rule_id, underscore_match.group()) is not None:
                lines_with_rule += 1
            else:
                lines_without_rule += 1
        self.assertGreaterEqual(lines_with_rule, 1)
        self.assertEqual(lines_without_rule, 0)
        self.assertIsNone(re.search(r'test\.py.*{}'.format(self.ruleset.python_parse_error.rule_id), output))
        self.assertIsNotNone(re.search(r'test\.py.*{}'.format(self.ruleset.python_wrap_html.rule_id), output))
        # Assert no rule totals.
        self.assertIsNone(re.search(r'{}:\s*{} violations'.format(self.ruleset.python_parse_error.rule_id, 0), output))
        # Assert final total
        self.assertIsNotNone(re.search(r'{} violations total'.format(5), output))

    def test_lint_with_verbose(self):
        """
        Tests the top-level linting with verbose option.
        """
        _lint(
            'scripts/xsslint/tests/templates',
            template_linters=self.template_linters,
            options={
                'list_files': False,
                'verbose': True,
                'rule_totals': False,
                'skip_dirs': ()
            },
            summary_results=self.summary_results,
            out=self.out,
        )

        output = self.out.getvalue()
        lines_with_rule = 0
        lines_without_rule = 0  # Output with verbose setting only.
        for underscore_match in re.finditer(r'test\.underscore:.*\n', output):
            if re.search(self.ruleset.underscore_not_escaped.rule_id, underscore_match.group()) is not None:
                lines_with_rule += 1
            else:
                lines_without_rule += 1
        self.assertGreaterEqual(lines_with_rule, 1)
        self.assertGreaterEqual(lines_without_rule, 1)
        # Assert no rule totals.
        self.assertIsNone(re.search(r'{}:\s*{} violations'.format(self.ruleset.python_parse_error.rule_id, 0), output))
        # Assert final total
        self.assertIsNotNone(re.search(r'{} violations total'.format(5), output))

    def test_lint_with_rule_totals(self):
        """
        Tests the top-level linting with rule totals option.
        """
        _lint(
            'scripts/xsslint/tests/templates',
            template_linters=self.template_linters,
            options={
                'list_files': False,
                'verbose': False,
                'rule_totals': True,
                'skip_dirs': ()
            },
            summary_results=self.summary_results,
            out=self.out,
        )

        output = self.out.getvalue()
        self.assertIsNotNone(re.search(r'test\.py.*{}'.format(self.ruleset.python_wrap_html.rule_id), output))

        # Assert totals output.
        self.assertIsNotNone(re.search(r'{}:\s*{} violations'.format(self.ruleset.python_parse_error.rule_id, 0), output))
        self.assertIsNotNone(re.search(r'{}:\s*{} violations'.format(self.ruleset.python_wrap_html.rule_id, 1), output))
        self.assertIsNotNone(re.search(r'{} violations total'.format(5), output))

    def test_lint_with_list_files(self):
        """
        Tests the top-level linting with list files option.
        """
        _lint(
            'scripts/xsslint/tests/templates',
            template_linters=self.template_linters,
            options={
                'list_files': True,
                'verbose': False,
                'rule_totals': False,
                'skip_dirs': ()
            },
            summary_results=self.summary_results,
            out=self.out,
        )

        output = self.out.getvalue()
        # Assert file with rule is not output.
        self.assertIsNone(re.search(r'test\.py.*{}'.format(self.ruleset.python_wrap_html.rule_id), output))
        # Assert file is output.
        self.assertIsNotNone(re.search(r'test\.py', output))

        # Assert no totals.
        self.assertIsNone(re.search(r'{}:\s*{} violations'.format(self.ruleset.python_parse_error.rule_id, 0), output))
        self.assertIsNone(re.search(r'{} violations total'.format(7), output))
