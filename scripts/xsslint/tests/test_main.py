# -*- coding: utf-8 -*-
"""
Tests for main.py
"""
import re
import textwrap
from StringIO import StringIO
from unittest import TestCase

import mock

from xsslint.linters import JavaScriptLinter, MakoTemplateLinter, PythonLinter, UnderscoreTemplateLinter
from xsslint.main import _lint
from xsslint.reporting import SummaryResults
from xsslint.rules import Rules


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

    def test_lint_defaults(self):
        """
        Tests the top-level linting with default options.
        """
        out = StringIO()
        summary_results = SummaryResults()

        _lint(
            'scripts/xsslint/tests/templates',
            template_linters=[MakoTemplateLinter(), UnderscoreTemplateLinter(), JavaScriptLinter(), PythonLinter()],
            options={
                'list_files': False,
                'verbose': False,
                'rule_totals': False,
            },
            summary_results=summary_results,
            out=out,
        )

        output = out.getvalue()
        # Assert violation details are displayed.
        self.assertIsNotNone(re.search('test\.html.*{}'.format(Rules.mako_missing_default.rule_id), output))
        self.assertIsNotNone(re.search('test\.coffee.*{}'.format(Rules.javascript_concat_html.rule_id), output))
        self.assertIsNotNone(re.search('test\.coffee.*{}'.format(Rules.underscore_not_escaped.rule_id), output))
        self.assertIsNotNone(re.search('test\.js.*{}'.format(Rules.javascript_concat_html.rule_id), output))
        self.assertIsNotNone(re.search('test\.js.*{}'.format(Rules.underscore_not_escaped.rule_id), output))
        lines_with_rule = 0
        lines_without_rule = 0  # Output with verbose setting only.
        for underscore_match in re.finditer('test\.underscore:.*\n', output):
            if re.search(Rules.underscore_not_escaped.rule_id, underscore_match.group()) is not None:
                lines_with_rule += 1
            else:
                lines_without_rule += 1
        self.assertGreaterEqual(lines_with_rule, 1)
        self.assertEquals(lines_without_rule, 0)
        self.assertIsNone(re.search('test\.py.*{}'.format(Rules.python_parse_error.rule_id), output))
        self.assertIsNotNone(re.search('test\.py.*{}'.format(Rules.python_wrap_html.rule_id), output))
        # Assert no rule totals.
        self.assertIsNone(re.search('{}:\s*{} violations'.format(Rules.python_parse_error.rule_id, 0), output))
        # Assert final total
        self.assertIsNotNone(re.search('{} violations total'.format(7), output))

    def test_lint_with_verbose(self):
        """
        Tests the top-level linting with verbose option.
        """
        out = StringIO()
        summary_results = SummaryResults()

        _lint(
            'scripts/xsslint/tests/templates',
            template_linters=[MakoTemplateLinter(), UnderscoreTemplateLinter(), JavaScriptLinter(), PythonLinter()],
            options={
                'list_files': False,
                'verbose': True,
                'rule_totals': False,
            },
            summary_results=summary_results,
            out=out,
        )

        output = out.getvalue()
        lines_with_rule = 0
        lines_without_rule = 0  # Output with verbose setting only.
        for underscore_match in re.finditer('test\.underscore:.*\n', output):
            if re.search(Rules.underscore_not_escaped.rule_id, underscore_match.group()) is not None:
                lines_with_rule += 1
            else:
                lines_without_rule += 1
        self.assertGreaterEqual(lines_with_rule, 1)
        self.assertGreaterEqual(lines_without_rule, 1)
        # Assert no rule totals.
        self.assertIsNone(re.search('{}:\s*{} violations'.format(Rules.python_parse_error.rule_id, 0), output))
        # Assert final total
        self.assertIsNotNone(re.search('{} violations total'.format(7), output))

    def test_lint_with_rule_totals(self):
        """
        Tests the top-level linting with rule totals option.
        """
        out = StringIO()
        summary_results = SummaryResults()

        _lint(
            'scripts/xsslint/tests/templates',
            template_linters=[MakoTemplateLinter(), UnderscoreTemplateLinter(), JavaScriptLinter(), PythonLinter()],
            options={
                'list_files': False,
                'verbose': False,
                'rule_totals': True,
            },
            summary_results=summary_results,
            out=out,
        )

        output = out.getvalue()
        self.assertIsNotNone(re.search('test\.py.*{}'.format(Rules.python_wrap_html.rule_id), output))

        # Assert totals output.
        self.assertIsNotNone(re.search('{}:\s*{} violations'.format(Rules.python_parse_error.rule_id, 0), output))
        self.assertIsNotNone(re.search('{}:\s*{} violations'.format(Rules.python_wrap_html.rule_id, 1), output))
        self.assertIsNotNone(re.search('{} violations total'.format(7), output))

    def test_lint_with_list_files(self):
        """
        Tests the top-level linting with list files option.
        """
        out = StringIO()
        summary_results = SummaryResults()

        _lint(
            'scripts/xsslint/tests/templates',
            template_linters=[MakoTemplateLinter(), UnderscoreTemplateLinter(), JavaScriptLinter(), PythonLinter()],
            options={
                'list_files': True,
                'verbose': False,
                'rule_totals': False,
            },
            summary_results=summary_results,
            out=out,
        )

        output = out.getvalue()
        # Assert file with rule is not output.
        self.assertIsNone(re.search('test\.py.*{}'.format(Rules.python_wrap_html.rule_id), output))
        # Assert file is output.
        self.assertIsNotNone(re.search('test\.py', output))

        # Assert no totals.
        self.assertIsNone(re.search('{}:\s*{} violations'.format(Rules.python_parse_error.rule_id, 0), output))
        self.assertIsNone(re.search('{} violations total'.format(7), output))
