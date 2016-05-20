# -*- coding: utf-8 -*-
"""
Tests for safe_template_linter.py
"""
from ddt import ddt, data
import mock
import re
from StringIO import StringIO
import textwrap
from unittest import TestCase

from scripts.safe_template_linter import (
    _lint, FileResults, JavaScriptLinter, MakoTemplateLinter, ParseString,
    StringLines, PythonLinter, SummaryResults, UnderscoreTemplateLinter, Rules
)


@ddt
class TestStringLines(TestCase):
    """
    Test StringLines class.
    """
    @data(
        {'string': 'test', 'index': 0, 'line_start_index': 0, 'line_end_index': 4},
        {'string': 'test', 'index': 2, 'line_start_index': 0, 'line_end_index': 4},
        {'string': 'test', 'index': 3, 'line_start_index': 0, 'line_end_index': 4},
        {'string': '\ntest', 'index': 0, 'line_start_index': 0, 'line_end_index': 1},
        {'string': '\ntest', 'index': 2, 'line_start_index': 1, 'line_end_index': 5},
        {'string': '\ntest\n', 'index': 0, 'line_start_index': 0, 'line_end_index': 1},
        {'string': '\ntest\n', 'index': 2, 'line_start_index': 1, 'line_end_index': 6},
        {'string': '\ntest\n', 'index': 6, 'line_start_index': 6, 'line_end_index': 6},
    )
    def test_string_lines_start_end_index(self, data):
        """
        Test StringLines index_to_line_start_index and index_to_line_end_index.
        """
        lines = StringLines(data['string'])
        self.assertEqual(lines.index_to_line_start_index(data['index']), data['line_start_index'])
        self.assertEqual(lines.index_to_line_end_index(data['index']), data['line_end_index'])

    @data(
        {'string': 'test', 'line_number': 1, 'line': 'test'},
        {'string': '\ntest', 'line_number': 1, 'line': ''},
        {'string': '\ntest', 'line_number': 2, 'line': 'test'},
        {'string': '\ntest\n', 'line_number': 1, 'line': ''},
        {'string': '\ntest\n', 'line_number': 2, 'line': 'test'},
        {'string': '\ntest\n', 'line_number': 3, 'line': ''},
    )
    def test_string_lines_start_end_index(self, data):
        """
        Test line_number_to_line.
        """
        lines = StringLines(data['string'])
        self.assertEqual(lines.line_number_to_line(data['line_number']), data['line'])


class TestLinter(TestCase):
    """
    Test Linter base class
    """
    def _validate_data_rules(self, data, results):
        """
        Validates that the appropriate rule violations were triggered.

        Arguments:
            data: A dict containing the 'rule' (or rules) to be tests.
            results: The results, containing violations to be validated.

        """
        rules = []
        if isinstance(data['rule'], list):
            rules = data['rule']
        elif data['rule'] is not None:
            rules.append(data['rule'])
        results.violations.sort(key=lambda violation: violation.sort_key())

        # Print violations if the lengths are different.
        if len(results.violations) != len(rules):
            for violation in results.violations:
                print("Found violation: {}".format(violation.rule))

        self.assertEqual(len(results.violations), len(rules))
        for violation, rule in zip(results.violations, rules):
            self.assertEqual(violation.rule, rule)


class TestSafeTemplateLinter(TestCase):
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

        patcher = mock.patch('scripts.safe_template_linter.is_skip_dir', return_value=False)
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
            'scripts/tests/templates',
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
            'scripts/tests/templates',
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
            'scripts/tests/templates',
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
            'scripts/tests/templates',
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


@ddt
class TestMakoTemplateLinter(TestLinter):
    """
    Test MakoTemplateLinter
    """

    @data(
        {'directory': 'lms/templates', 'expected': True},
        {'directory': 'lms/templates/support', 'expected': True},
        {'directory': 'lms/templates/support', 'expected': True},
        {'directory': 'test_root/staticfiles/templates', 'expected': False},
        {'directory': './test_root/staticfiles/templates', 'expected': False},
        {'directory': './some/random/path', 'expected': False},
    )
    def test_is_valid_directory(self, data):
        """
        Test _is_valid_directory correctly determines mako directories
        """
        linter = MakoTemplateLinter()

        self.assertEqual(linter._is_valid_directory(data['directory']), data['expected'])

    @data(
        {
            'template': '\n <%page expression_filter="h"/>',
            'rule': None
        },
        {
            'template':
                '\n <%page args="section_data" expression_filter="h" /> ',
            'rule': None
        },
        {
            'template': '\n ## <%page expression_filter="h"/>',
            'rule': Rules.mako_missing_default
        },
        {
            'template':
                '\n <%page expression_filter="h" /> '
                '\n <%page args="section_data"/>',
            'rule': Rules.mako_multiple_page_tags
        },
        {
            'template':
                '\n <%page expression_filter="h" /> '
                '\n ## <%page args="section_data"/>',
            'rule': None
        },
        {
            'template': '\n <%page args="section_data" /> ',
            'rule': Rules.mako_missing_default
        },
        {
            'template':
                '\n <%page args="section_data"/> <some-other-tag expression_filter="h" /> ',
            'rule': Rules.mako_missing_default
        },
        {
            'template': '\n',
            'rule': Rules.mako_missing_default
        },
    )
    def test_check_page_default(self, data):
        """
        Test _check_mako_file_is_safe with different page defaults
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        linter._check_mako_file_is_safe(data['template'], results)

        num_violations = 0 if data['rule'] is None else 1
        self.assertEqual(len(results.violations), num_violations)
        if num_violations > 0:
            self.assertEqual(results.violations[0].rule, data['rule'])

    @data(
        {'expression': '${x}', 'rule': None},
        {'expression': '${{unbalanced}', 'rule': Rules.mako_unparseable_expression},
        {'expression': '${x | n}', 'rule': Rules.mako_invalid_html_filter},
        {'expression': '${x | n, decode.utf8}', 'rule': None},
        {'expression': '${x | h}', 'rule': Rules.mako_unwanted_html_filter},
        {'expression': '  ## ${commented_out | h}', 'rule': None},
        {'expression': '${x | n, dump_js_escaped_json}', 'rule': Rules.mako_invalid_html_filter},
    )
    def test_check_mako_expressions_in_html(self, data):
        """
        Test _check_mako_file_is_safe in html context provides appropriate violations
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            {expression}
        """.format(expression=data['expression']))

        linter._check_mako_file_is_safe(mako_template, results)

        self._validate_data_rules(data, results)

    def test_check_mako_expression_display_name(self):
        """
        Test _check_mako_file_is_safe with display_name_with_default_escaped
        fails.
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            ${course.display_name_with_default_escaped}
        """)

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), 1)
        self.assertEqual(results.violations[0].rule, Rules.python_deprecated_display_name)

    @data(
        {
            # Python blocks between <% ... %> use the same Python linting as
            # Mako expressions between ${ ... }. This single test verifies
            # that these blocks are linted. The individual linting rules are
            # tested in the Mako expression tests that follow.
            'expression':
                textwrap.dedent("""
                    <%
                        a_link_start = '<a class="link-courseURL" rel="external" href="'
                        a_link_end = '">' + _("your course summary page") + '</a>'
                        a_link = a_link_start + lms_link_for_about_page + a_link_end
                        text = _("Introductions, prerequisites, FAQs that are used on %s (formatted in HTML)") % a_link
                    %>
                """),
            'rule': [Rules.python_wrap_html, Rules.python_concat_html, Rules.python_wrap_html]
        },
        {
            'expression':
                textwrap.dedent("""
                    ${"Mixed {span_start}text{span_end}".format(
                        span_start=HTML("<span>"),
                        span_end=HTML("</span>"),
                    )}
                """),
            'rule': Rules.python_requires_html_or_text
        },
        {
            'expression':
                textwrap.dedent("""
                    ${Text("Mixed {span_start}text{span_end}").format(
                        span_start=HTML("<span>"),
                        span_end=HTML("</span>"),
                    )}
                """),
            'rule': None
        },
        {
            'expression':
                textwrap.dedent("""
                    ${"Mixed {span_start}{text}{span_end}".format(
                        span_start=HTML("<span>"),
                        text=Text("This should still break."),
                        span_end=HTML("</span>"),
                    )}
                """),
            'rule': Rules.python_requires_html_or_text
        },
        {
            'expression':
                textwrap.dedent("""
                    ${Text("Mixed {link_start}text{link_end}".format(
                        link_start=HTML("<a href='{}'>").format(url),
                        link_end=HTML("</a>"),
                    ))}
                """),
            'rule': [Rules.python_close_before_format, Rules.python_requires_html_or_text]
        },
        {
            'expression':
                textwrap.dedent("""
                    ${Text("Mixed {link_start}text{link_end}").format(
                        link_start=HTML("<a href='{}'>".format(url)),
                        link_end=HTML("</a>"),
                    )}
                """),
            'rule': Rules.python_close_before_format
        },
        {
            'expression':
                textwrap.dedent("""
                    ${"Mixed {span_start}text{span_end}".format(
                        span_start="<span>",
                        span_end="</span>",
                    )}
                """),
            'rule': [Rules.python_wrap_html, Rules.python_wrap_html]
        },
        {
            'expression':
                textwrap.dedent("""
                    ${Text(_("String with multiple lines "
                        "{link_start}unenroll{link_end} "
                        "and final line")).format(
                            link_start=HTML(
                                '<a id="link__over_multiple_lines" '
                                'data-course-id="{course_id}" '
                                'href="#test-modal">'
                            ).format(
                                course_id=course_overview.id
                            ),
                            link_end=HTML('</a>'),
                    )}
                """),
            'rule': None
        },
        {
            'expression': "${'<span></span>'}",
            'rule': Rules.python_wrap_html
        },
        {
            'expression': "${'Embedded HTML <strong></strong>'}",
            'rule': Rules.python_wrap_html
        },
        {
            'expression': "${ HTML('<span></span>') }",
            'rule': None
        },
        {
            'expression': "${HTML(render_entry(map['entries'], child))}",
            'rule': None
        },
        {
            'expression': "${ '<span></span>' + 'some other text' }",
            'rule': [Rules.python_concat_html, Rules.python_wrap_html]
        },
        {
            'expression': "${ HTML('<span>missing closing parentheses.</span>' }",
            'rule': Rules.python_parse_error
        },
        {
            'expression': "${'Rock &amp; Roll'}",
            'rule': Rules.mako_html_entities
        },
        {
            'expression': "${'Rock &#38; Roll'}",
            'rule': Rules.mako_html_entities
        },
    )
    def test_check_mako_with_text_and_html(self, data):
        """
        Test _check_mako_file_is_safe tests for proper use of Text() and Html().
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            {expression}
        """.format(expression=data['expression']))

        linter._check_mako_file_is_safe(mako_template, results)

        self._validate_data_rules(data, results)

    def test_check_mako_entity_with_no_default(self):
        """
        Test _check_mako_file_is_safe does not fail on entities when
        safe-by-default is not set.
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = "${'Rock &#38; Roll'}"

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), 1)
        self.assertEqual(results.violations[0].rule, Rules.mako_missing_default)

    def test_check_mako_expression_default_disabled(self):
        """
        Test _check_mako_file_is_safe with disable pragma for safe-by-default
        works to designate that this is not a Mako file
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            # This is anything but a Mako file.

            # pragma can appear anywhere in file
            # safe-lint: disable=mako-missing-default
        """)

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), 1)
        self.assertTrue(results.violations[0].is_disabled)

    def test_check_mako_expression_disabled(self):
        """
        Test _check_mako_file_is_safe with disable pragma results in no
        violation
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            ## safe-lint: disable=mako-unwanted-html-filter
            ${x | h}
        """)

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), 1)
        self.assertTrue(results.violations[0].is_disabled)

    @data(
        {'template': '{% extends "wiki/base.html" %}'},
        {'template': '{{ message }}'},
    )
    def test_check_mako_on_django_template(self, data):
        """
        Test _check_mako_file_is_safe with disable pragma results in no
        violation
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        linter._check_mako_file_is_safe(data['template'], results)

        self.assertEqual(len(results.violations), 0)

    def test_check_mako_expressions_in_html_without_default(self):
        """
        Test _check_mako_file_is_safe in html context without the page level
        default h filter suppresses expression level violation
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            ${x | h}
        """)

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), 1)
        self.assertEqual(results.violations[0].rule, Rules.mako_missing_default)

    @data(
        {'expression': '${x}', 'rule': Rules.mako_invalid_js_filter},
        {'expression': '${{unbalanced}', 'rule': Rules.mako_unparseable_expression},
        {'expression': '${x | n}', 'rule': Rules.mako_invalid_js_filter},
        {'expression': '${x | h}', 'rule': Rules.mako_invalid_js_filter},
        {'expression': '${x | n, dump_js_escaped_json}', 'rule': None},
        {'expression': '${x | n, decode.utf8}', 'rule': None},
    )
    def test_check_mako_expressions_in_javascript(self, data):
        """
        Test _check_mako_file_is_safe in JavaScript script context provides
        appropriate violations
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            ## switch to JavaScript context
            <script>
                {expression}
            </script>
            ## switch back to HTML context
            ${{x}}
        """.format(expression=data['expression']))

        linter._check_mako_file_is_safe(mako_template, results)

        self._validate_data_rules(data, results)

    @data(
        {'expression': '${x}', 'rule': Rules.mako_invalid_js_filter},
        {'expression': '"${x | n, js_escaped_string}"', 'rule': None},
    )
    def test_check_mako_expressions_in_require_module(self, data):
        """
        Test _check_mako_file_is_safe in JavaScript require context provides
        appropriate violations
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            ## switch to JavaScript context (after next line)
            <%static:require_module module_name="${{x}}" class_name="TestFactory">
                {expression}
            </%static:require_module>
            ## switch back to HTML context
            ${{x}}
        """.format(expression=data['expression']))

        linter._check_mako_file_is_safe(mako_template, results)

        self._validate_data_rules(data, results)

    @data(
        {'expression': '${x}', 'rule': Rules.mako_invalid_js_filter},
        {'expression': '"${x | n, js_escaped_string}"', 'rule': None},
    )
    def test_check_mako_expressions_in_require_js(self, data):
        """
        Test _check_mako_file_is_safe in JavaScript require js context provides
        appropriate violations
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            # switch to JavaScript context
            <%block name="requirejs">
                {expression}
            </%block>
            ## switch back to HTML context
            ${{x}}
        """.format(expression=data['expression']))

        linter._check_mako_file_is_safe(mako_template, results)

        self._validate_data_rules(data, results)

    @data(
        {'media_type': 'text/javascript', 'rule': None},
        {'media_type': 'text/ecmascript', 'rule': None},
        {'media_type': 'application/ecmascript', 'rule': None},
        {'media_type': 'application/javascript', 'rule': None},
        {'media_type': 'text/x-mathjax-config', 'rule': None},
        {'media_type': 'json/xblock-args', 'rule': None},
        {'media_type': 'text/template', 'rule': Rules.mako_invalid_html_filter},
        {'media_type': 'unknown/type', 'rule': Rules.mako_unknown_context},
    )
    def test_check_mako_expressions_in_script_type(self, data):
        """
        Test _check_mako_file_is_safe in script tag with different media types
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            # switch to JavaScript context
            <script type="{}">
                ${{x | n, dump_js_escaped_json}}
            </script>
            ## switch back to HTML context
            ${{x}}
        """).format(data['media_type'])

        linter._check_mako_file_is_safe(mako_template, results)

        self._validate_data_rules(data, results)

    def test_check_mako_expressions_in_mixed_contexts(self):
        """
        Test _check_mako_file_is_safe in mixed contexts provides
        appropriate violations
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            ${x | h}
            <script type="text/javascript">
                ${x | h}
            </script>
            ${x | h}
            <%static:require_module module_name="${x}" class_name="TestFactory">
                ${x | h}
            </%static:require_module>
            ${x | h}
        """)

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), 5)
        self.assertEqual(results.violations[0].rule, Rules.mako_unwanted_html_filter)
        self.assertEqual(results.violations[1].rule, Rules.mako_invalid_js_filter)
        self.assertEqual(results.violations[2].rule, Rules.mako_unwanted_html_filter)
        self.assertEqual(results.violations[3].rule, Rules.mako_invalid_js_filter)
        self.assertEqual(results.violations[4].rule, Rules.mako_unwanted_html_filter)

    def test_check_mako_expressions_javascript_strings(self):
        """
        Test _check_mako_file_is_safe javascript string specific rules.
        - mako_js_missing_quotes
        - mako_js_html_string
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            <script type="text/javascript">
                var valid1 = '${x | n, js_escaped_string} ${y | n, js_escaped_string}'
                var valid2 = '${x | n, js_escaped_string} ${y | n, js_escaped_string}'
                var valid3 = 'string' + ' ${x | n, js_escaped_string} '
                var valid4 = "${Text(_('Some mixed text{begin_span}with html{end_span}')).format(
                    begin_span=HTML('<span>'),
                    end_span=HTML('</span>'),
                ) | n, js_escaped_string}"
                var valid5 = " " + "${Text(_('Please {link_start}send us e-mail{link_end}.')).format(
                    link_start=HTML('<a href="#" id="feedback_email">'),
                    link_end=HTML('</a>'),
                ) | n, js_escaped_string}";
                var invalid1 = ${x | n, js_escaped_string};
                var invalid2 = '<strong>${x | n, js_escaped_string}</strong>'
                var invalid3 = '<strong>${x | n, dump_js_escaped_json}</strong>'
            </script>
        """)

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), 3)
        self.assertEqual(results.violations[0].rule, Rules.mako_js_missing_quotes)
        self.assertEqual(results.violations[1].rule, Rules.mako_js_html_string)
        self.assertEqual(results.violations[2].rule, Rules.mako_js_html_string)

    def test_check_javascript_in_mako_javascript_context(self):
        """
        Test _check_mako_file_is_safe with JavaScript error in JavaScript
        context.
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            <script type="text/javascript">
                var message = '<p>' + msg + '</p>';
            </script>
        """)

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), 1)
        self.assertEqual(results.violations[0].rule, Rules.javascript_concat_html)
        self.assertEqual(results.violations[0].start_line, 4)

    @data(
        {'template': "\n${x | n}", 'parseable': True},
        {
            'template': textwrap.dedent(
                """
                    <div>${(
                        'tabbed-multi-line-expression'
                    ) | n}</div>
                """),
            'parseable': True
        },
        {'template': "${{unparseable}", 'parseable': False},
    )
    def test_expression_detailed_results(self, data):
        """
        Test _check_mako_file_is_safe provides detailed results, including line
        numbers, columns, and line
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        linter._check_mako_file_is_safe(data['template'], results)

        self.assertEqual(len(results.violations), 2)
        self.assertEqual(results.violations[0].rule, Rules.mako_missing_default)

        violation = results.violations[1]
        lines = list(data['template'].splitlines())
        self.assertTrue("${" in lines[violation.start_line - 1])
        self.assertTrue(lines[violation.start_line - 1].startswith("${", violation.start_column - 1))
        if data['parseable']:
            self.assertTrue("}" in lines[violation.end_line - 1])
            self.assertTrue(lines[violation.end_line - 1].startswith("}", violation.end_column - len("}") - 1))
        else:
            self.assertEqual(violation.start_line, violation.end_line)
            self.assertEqual(violation.end_column, "?")
        self.assertEqual(len(violation.lines), violation.end_line - violation.start_line + 1)
        for line_index in range(0, len(violation.lines)):
            self.assertEqual(violation.lines[line_index], lines[line_index + violation.start_line - 1])

    @data(
        {'template': "${x}"},
        {'template': "\n ${x}"},
        {'template': "${x} "},
        {'template': "${{test-balanced-delims}} "},
        {'template': "${'{unbalanced in string'}"},
        {'template': "${'unbalanced in string}'}"},
        {'template': "${(\n    'tabbed-multi-line-expression'\n  )}"},
    )
    def test_find_mako_expressions(self, data):
        """
        Test _find_mako_expressions for parseable expressions
        """
        linter = MakoTemplateLinter()

        expressions = linter._find_mako_expressions(data['template'])

        self.assertEqual(len(expressions), 1)
        start_index = expressions[0].start_index
        end_index = expressions[0].end_index
        self.assertEqual(data['template'][start_index:end_index], data['template'].strip())
        self.assertEqual(expressions[0].expression, data['template'].strip())

    @data(
        {'template': " ${{unparseable} ${}", 'start_index': 1},
        {'template': " ${'unparseable} ${}", 'start_index': 1},
    )
    def test_find_unparseable_mako_expressions(self, data):
        """
        Test _find_mako_expressions for unparseable expressions
        """
        linter = MakoTemplateLinter()

        expressions = linter._find_mako_expressions(data['template'])
        self.assertTrue(2 <= len(expressions))
        self.assertEqual(expressions[0].start_index, data['start_index'])
        self.assertIsNone(expressions[0].expression)

    @data(
        {
            'template': '${""}',
            'result': {'start_index': 2, 'end_index': 4, 'quote_length': 1}
        },
        {
            'template': "${''}",
            'result': {'start_index': 2, 'end_index': 4, 'quote_length': 1}
        },
        {
            'template': "${'Hello'}",
            'result': {'start_index': 2, 'end_index': 9, 'quote_length': 1}
        },
        {
            'template': '${""" triple """}',
            'result': {'start_index': 2, 'end_index': 16, 'quote_length': 3}
        },
        {
            'template': r""" ${" \" \\"} """,
            'result': {'start_index': 3, 'end_index': 11, 'quote_length': 1}
        },
        {
            'template': "${'broken string}",
            'result': {'start_index': 2, 'end_index': None, 'quote_length': None}
        },
    )
    def test_parse_string(self, data):
        """
        Test _parse_string helper
        """
        linter = MakoTemplateLinter()

        parse_string = ParseString(data['template'], data['result']['start_index'], len(data['template']))
        string_dict = {
            'start_index': parse_string.start_index,
            'end_index': parse_string.end_index,
            'quote_length': parse_string.quote_length,
        }

        self.assertDictEqual(string_dict, data['result'])
        if parse_string.end_index is not None:
            self.assertEqual(data['template'][parse_string.start_index:parse_string.end_index], parse_string.string)
            start_inner_index = parse_string.start_index + parse_string.quote_length
            end_inner_index = parse_string.end_index - parse_string.quote_length
            self.assertEqual(data['template'][start_inner_index:end_inner_index], parse_string.string_inner)


@ddt
class TestUnderscoreTemplateLinter(TestLinter):
    """
    Test UnderscoreTemplateLinter
    """

    def test_check_underscore_file_is_safe(self):
        """
        Test check_underscore_file_is_safe with safe template
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        template = textwrap.dedent("""
            <%- gettext('Single Line') %>

            <%-
                gettext('Multiple Lines')
            %>
        """)

        linter.check_underscore_file_is_safe(template, results)

        self.assertEqual(len(results.violations), 0)

    def test_check_underscore_file_is_not_safe(self):
        """
        Test check_underscore_file_is_safe with unsafe template
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        template = textwrap.dedent("""
            <%= gettext('Single Line') %>

            <%=
                gettext('Multiple Lines')
            %>
        """)

        linter.check_underscore_file_is_safe(template, results)

        self.assertEqual(len(results.violations), 2)
        self.assertEqual(results.violations[0].rule, Rules.underscore_not_escaped)
        self.assertEqual(results.violations[1].rule, Rules.underscore_not_escaped)

    @data(
        {
            'template':
                '<% // safe-lint:   disable=underscore-not-escaped   %>\n'
                '<%= message %>',
            'is_disabled': [True],
        },
        {
            'template':
                '<% // safe-lint: disable=another-rule,underscore-not-escaped %>\n'
                '<%= message %>',
            'is_disabled': [True],
        },
        {
            'template':
                '<% // safe-lint: disable=another-rule %>\n'
                '<%= message %>',
            'is_disabled': [False],
        },
        {
            'template':
                '<% // safe-lint: disable=underscore-not-escaped %>\n'
                '<%= message %>\n'
                '<%= message %>',
            'is_disabled': [True, False],
        },
        {
            'template':
                '// This test does not use proper Underscore.js Template syntax\n'
                '// But, it is just testing that a maximum of 5 non-whitespace\n'
                '// are used to designate start of line for disabling the next line.\n'
                ' 1 2 3 4 5 safe-lint: disable=underscore-not-escaped %>\n'
                '<%= message %>\n'
                ' 1 2 3 4 5 6 safe-lint: disable=underscore-not-escaped %>\n'
                '<%= message %>',
            'is_disabled': [True, False],
        },
        {
            'template':
                '<%= message %><% // safe-lint: disable=underscore-not-escaped %>\n'
                '<%= message %>',
            'is_disabled': [True, False],
        },
        {
            'template':
                '<%= message %>\n'
                '<% // safe-lint: disable=underscore-not-escaped %>',
            'is_disabled': [False],
        },
    )
    def test_check_underscore_file_disable_rule(self, data):
        """
        Test check_underscore_file_is_safe with various disabled pragmas
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        linter.check_underscore_file_is_safe(data['template'], results)

        violation_count = len(data['is_disabled'])
        self.assertEqual(len(results.violations), violation_count)
        for index in range(0, violation_count - 1):
            self.assertEqual(results.violations[index].is_disabled, data['is_disabled'][index])

    def test_check_underscore_file_disables_one_violation(self):
        """
        Test check_underscore_file_is_safe with disabled before a line only
        disables for the violation following
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        template = textwrap.dedent("""
            <% // safe-lint: disable=underscore-not-escaped %>
            <%= message %>
            <%= message %>
        """)

        linter.check_underscore_file_is_safe(template, results)

        self.assertEqual(len(results.violations), 2)
        self.assertEqual(results.violations[0].is_disabled, True)
        self.assertEqual(results.violations[1].is_disabled, False)

    @data(
        {'template': '<%= HtmlUtils.ensureHtml(message) %>'},
        {'template': '<%= _.escape(message) %>'},
    )
    def test_check_underscore_no_escape_allowed(self, data):
        """
        Test check_underscore_file_is_safe with expressions that are allowed
        without escaping because the internal calls properly escape.
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        linter.check_underscore_file_is_safe(data['template'], results)

        self.assertEqual(len(results.violations), 0)


@ddt
class TestJavaScriptLinter(TestLinter):
    """
    Test JavaScriptLinter
    """
    @data(
        {'template': 'var m = "Plain text " + message + "plain text"', 'rule': None},
        {'template': 'var m = "檌檒濦 " + message + "plain text"', 'rule': None},
        {
            'template':
                ("""$email_header.append($('<input>', type: "button", name: "copy-email-body-text","""
                 """ value: gettext("Copy Email To Editor"), id: 'copy_email_' + email_id))"""),
            'rule': None
        },
        {'template': 'var m = "<p>" + message + "</p>"', 'rule': Rules.javascript_concat_html},
        {
            'template': r'var m = "<p>\"escaped quote\"" + message + "\"escaped quote\"</p>"',
            'rule': Rules.javascript_concat_html
        },
        {'template': '  // var m = "<p>" + commentedOutMessage + "</p>"', 'rule': None},
        {'template': 'var m = " <p> " + message + " </p> "', 'rule': Rules.javascript_concat_html},
        {'template': 'var m = " <p> " + message + " broken string', 'rule': Rules.javascript_concat_html},
    )
    def test_concat_with_html(self, data):
        """
        Test check_javascript_file_is_safe with concatenating strings and HTML
        """
        linter = JavaScriptLinter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)
        self._validate_data_rules(data, results)

    @data(
        {'template': 'test.append( test.render().el )', 'rule': None},
        {'template': 'test.append(test.render().el)', 'rule': None},
        {'template': 'test.append(test.render().$el)', 'rule': None},
        {'template': 'test.append(testEl)', 'rule': None},
        {'template': 'test.append($test)', 'rule': None},
        # plain text is ok because any & will be escaped, and it stops false
        # negatives on some other objects with an append() method
        {'template': 'test.append("plain text")', 'rule': None},
        {'template': 'test.append("<div/>")', 'rule': Rules.javascript_jquery_append},
        {'template': 'graph.svg.append("g")', 'rule': None},
        {'template': 'test.append( $( "<div>" ) )', 'rule': None},
        {'template': 'test.append($("<div>"))', 'rule': None},
        {'template': 'test.append($("<div/>"))', 'rule': None},
        {'template': 'test.append(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'HtmlUtils.append($el, someHtml)', 'rule': None},
        {'template': 'test.append("fail on concat" + test.render().el)', 'rule': Rules.javascript_jquery_append},
        {'template': 'test.append("fail on concat" + testEl)', 'rule': Rules.javascript_jquery_append},
        {'template': 'test.append(message)', 'rule': Rules.javascript_jquery_append},
    )
    def test_jquery_append(self, data):
        """
        Test check_javascript_file_is_safe with JQuery append()
        """
        linter = JavaScriptLinter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)

    @data(
        {'template': 'test.prepend( test.render().el )', 'rule': None},
        {'template': 'test.prepend(test.render().el)', 'rule': None},
        {'template': 'test.prepend(test.render().$el)', 'rule': None},
        {'template': 'test.prepend(testEl)', 'rule': None},
        {'template': 'test.prepend($test)', 'rule': None},
        {'template': 'test.prepend("text")', 'rule': None},
        {'template': 'test.prepend( $( "<div>" ) )', 'rule': None},
        {'template': 'test.prepend($("<div>"))', 'rule': None},
        {'template': 'test.prepend($("<div/>"))', 'rule': None},
        {'template': 'test.prepend(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'HtmlUtils.prepend($el, someHtml)', 'rule': None},
        {'template': 'test.prepend("broken string)', 'rule': Rules.javascript_jquery_prepend},
        {'template': 'test.prepend("fail on concat" + test.render().el)', 'rule': Rules.javascript_jquery_prepend},
        {'template': 'test.prepend("fail on concat" + testEl)', 'rule': Rules.javascript_jquery_prepend},
        {'template': 'test.prepend(message)', 'rule': Rules.javascript_jquery_prepend},
    )
    def test_jquery_prepend(self, data):
        """
        Test check_javascript_file_is_safe with JQuery prepend()
        """
        linter = JavaScriptLinter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)

    @data(
        {'template': 'test.unwrap(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.wrap(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.wrapAll(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.wrapInner(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.after(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.before(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.replaceAll(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.replaceWith(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'test.replaceWith(edx.HtmlUtils.HTML(htmlString).toString())', 'rule': None},
        {'template': 'test.unwrap(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.wrap(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.wrapAll(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.wrapInner(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.after(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.before(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.replaceAll(anything)', 'rule': Rules.javascript_jquery_insertion},
        {'template': 'test.replaceWith(anything)', 'rule': Rules.javascript_jquery_insertion},
    )
    def test_jquery_insertion(self, data):
        """
        Test check_javascript_file_is_safe with JQuery insertion functions
        other than append(), prepend() and html() that take content as an
        argument (e.g. before(), after()).
        """
        linter = JavaScriptLinter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)

    @data(
        {'template': '  element.parentNode.appendTo(target);', 'rule': None},
        {'template': '  test.render().el.appendTo(target);', 'rule': None},
        {'template': '  test.render().$el.appendTo(target);', 'rule': None},
        {'template': '  test.$element.appendTo(target);', 'rule': None},
        {'template': '  test.testEl.appendTo(target);', 'rule': None},
        {'template': '$element.appendTo(target);', 'rule': None},
        {'template': 'el.appendTo(target);', 'rule': None},
        {'template': 'testEl.appendTo(target);', 'rule': None},
        {'template': 'testEl.prependTo(target);', 'rule': None},
        {'template': 'testEl.insertAfter(target);', 'rule': None},
        {'template': 'testEl.insertBefore(target);', 'rule': None},
        {'template': 'anycall().appendTo(target)', 'rule': Rules.javascript_jquery_insert_into_target},
        {'template': 'anything.appendTo(target)', 'rule': Rules.javascript_jquery_insert_into_target},
        {'template': 'anything.prependTo(target)', 'rule': Rules.javascript_jquery_insert_into_target},
        {'template': 'anything.insertAfter(target)', 'rule': Rules.javascript_jquery_insert_into_target},
        {'template': 'anything.insertBefore(target)', 'rule': Rules.javascript_jquery_insert_into_target},
    )
    def test_jquery_insert_to_target(self, data):
        """
        Test check_javascript_file_is_safe with JQuery insert to target
        functions that take a target as an argument, like appendTo() and
        prependTo().
        """
        linter = JavaScriptLinter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)

    @data(
        {'template': 'test.html()', 'rule': None},
        {'template': 'test.html( )', 'rule': None},
        {'template': "test.html( '' )", 'rule': None},
        {'template': "test.html('')", 'rule': None},
        {'template': 'test.html("")', 'rule': None},
        {'template': 'test.html(HtmlUtils.ensureHtml(htmlSnippet).toString())', 'rule': None},
        {'template': 'HtmlUtils.setHtml($el, someHtml)', 'rule': None},
        {'template': 'test.html("any string")', 'rule': Rules.javascript_jquery_html},
        {'template': 'test.html("broken string)', 'rule': Rules.javascript_jquery_html},
        {'template': 'test.html("檌檒濦")', 'rule': Rules.javascript_jquery_html},
        {'template': 'test.html(anything)', 'rule': Rules.javascript_jquery_html},
    )
    def test_jquery_html(self, data):
        """
        Test check_javascript_file_is_safe with JQuery html()
        """
        linter = JavaScriptLinter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)
        self._validate_data_rules(data, results)

    @data(
        {'template': 'StringUtils.interpolate()', 'rule': None},
        {'template': 'HtmlUtils.interpolateHtml()', 'rule': None},
        {'template': 'interpolate(anything)', 'rule': Rules.javascript_interpolate},
    )
    def test_javascript_interpolate(self, data):
        """
        Test check_javascript_file_is_safe with interpolate()
        """
        linter = JavaScriptLinter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)

    @data(
        {'template': '_.escape(message)', 'rule': None},
        {'template': 'anything.escape(message)', 'rule': Rules.javascript_escape},
    )
    def test_javascript_interpolate(self, data):
        """
        Test check_javascript_file_is_safe with interpolate()
        """
        linter = JavaScriptLinter()
        results = FileResults('')

        linter.check_javascript_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)


@ddt
class TestPythonLinter(TestLinter):
    """
    Test PythonLinter
    """
    @data(
        {'template': 'm = "Plain text " + message + "plain text"', 'rule': None},
        {'template': 'm = "檌檒濦 " + message + "plain text"', 'rule': None},
        {'template': '  # m = "<p>" + commentedOutMessage + "</p>"', 'rule': None},
        {'template': 'm = "<p>" + message + "</p>"', 'rule': [Rules.python_concat_html, Rules.python_concat_html]},
        {'template': 'm = " <p> " + message + " </p> "', 'rule': [Rules.python_concat_html, Rules.python_concat_html]},
        {'template': 'm = " <p> " + message + " broken string', 'rule': Rules.python_parse_error},
    )
    def test_concat_with_html(self, data):
        """
        Test check_python_file_is_safe with concatenating strings and HTML
        """
        linter = PythonLinter()
        results = FileResults('')

        linter.check_python_file_is_safe(data['template'], results)

        self._validate_data_rules(data, results)

    def test_check_python_expression_display_name(self):
        """
        Test _check_python_file_is_safe with display_name_with_default_escaped
        fails.
        """
        linter = PythonLinter()
        results = FileResults('')

        python_file = textwrap.dedent("""
            context = {
                'display_name': self.display_name_with_default_escaped,
            }
        """)

        linter.check_python_file_is_safe(python_file, results)

        self.assertEqual(len(results.violations), 1)
        self.assertEqual(results.violations[0].rule, Rules.python_deprecated_display_name)

    def test_check_custom_escaping(self):
        """
        Test _check_python_file_is_safe fails when custom escapins is used.
        """
        linter = PythonLinter()
        results = FileResults('')

        python_file = textwrap.dedent("""
            msg = mmlans.replace('<', '&lt;')
        """)

        linter.check_python_file_is_safe(python_file, results)

        self.assertEqual(len(results.violations), 1)
        self.assertEqual(results.violations[0].rule, Rules.python_custom_escape)

    @data(
        {
            'python':
                textwrap.dedent("""
                    msg = Text("Mixed {span_start}text{span_end}").format(
                        span_start=HTML("<span>"),
                        span_end=HTML("</span>"),
                    )
                """),
            'rule': None
        },
        {
            'python':
                textwrap.dedent("""
                    msg = "Mixed {span_start}text{span_end}".format(
                        span_start=HTML("<span>"),
                        span_end=HTML("</span>"),
                    )
                """),
            'rule': Rules.python_requires_html_or_text
        },
        {
            'python':
                textwrap.dedent("""
                    msg = "Mixed {span_start}{text}{span_end}".format(
                        span_start=HTML("<span>"),
                        text=Text("This should still break."),
                        span_end=HTML("</span>"),
                    )
                """),
            'rule': Rules.python_requires_html_or_text
        },
        {
            'python':
                textwrap.dedent("""
                    msg = Text("Mixed {link_start}text{link_end}".format(
                        link_start=HTML("<a href='{}'>").format(url),
                        link_end=HTML("</a>"),
                    ))
                """),
            'rule': [Rules.python_close_before_format, Rules.python_requires_html_or_text]
        },
        {
            'python':
                textwrap.dedent("""
                    msg = Text("Mixed {link_start}text{link_end}").format(
                        link_start=HTML("<a href='{}'>".format(url)),
                        link_end=HTML("</a>"),
                    )
                """),
            'rule': Rules.python_close_before_format
        },
        {
            'python':
                textwrap.dedent("""
                    msg = Text("Mixed {link_start}text{link_end}".format(
                        link_start=HTML("<a href='{}'>".format(HTML('<b>'))),
                        link_end=HTML("</a>"),
                    ))
                """),
            'rule':
                [
                    Rules.python_close_before_format,
                    Rules.python_requires_html_or_text,
                    Rules.python_close_before_format,
                    Rules.python_requires_html_or_text
                ]
        },
        {
            'python':
                textwrap.dedent("""
                    msg = "Mixed {span_start}text{span_end}".format(
                        span_start="<span>",
                        span_end="</span>",
                    )
                """),
            'rule': [Rules.python_wrap_html, Rules.python_wrap_html]
        },
        {
            'python':
                textwrap.dedent("""
                    msg = Text(_("String with multiple lines "
                        "{link_start}unenroll{link_end} "
                        "and final line")).format(
                            link_start=HTML(
                                '<a id="link__over_multiple_lines" '
                                'data-course-id="{course_id}" '
                                'href="#test-modal">'
                            ).format(
                                # Line comment with ' to throw off parser
                                course_id=course_overview.id
                            ),
                            link_end=HTML('</a>'),
                    )
                """),
            'rule': None
        },
        {
            'python': "msg = '<span></span>'",
            'rule': None
        },
        {
            'python': "msg = HTML('<span></span>')",
            'rule': None
        },
        {
            'python': r"""msg = '<a href="{}"'.format(url)""",
            'rule': Rules.python_wrap_html
        },
        {
            'python': r"""msg = '{}</p>'.format(message)""",
            'rule': Rules.python_wrap_html
        },
        {
            'python': r"""r'regex with {} and named group(?P<id>\d+)?$'.format(test)""",
            'rule': None
        },
        {
            'python': r"""msg = '<a href="%s"' % url""",
            'rule': Rules.python_interpolate_html
        },
        {
            'python':
                textwrap.dedent("""
                    def __repr__(self):
                        # Assume repr implementations are safe, and not HTML
                        return '<CCXCon {}>'.format(self.title)
                """),
            'rule': None
        },
        {
            'python': r"""msg = '%s</p>' % message""",
            'rule': Rules.python_interpolate_html
        },
        {
            'python': "msg = HTML('<span></span>'",
            'rule': Rules.python_parse_error
        },
    )
    def test_check_python_with_text_and_html(self, data):
        """
        Test _check_python_file_is_safe tests for proper use of Text() and
        Html().

        """
        linter = PythonLinter()
        results = FileResults('')

        file_content = textwrap.dedent(data['python'])

        linter.check_python_file_is_safe(file_content, results)

        self._validate_data_rules(data, results)

    def test_check_python_with_text_and_html_mixed(self):
        """
        Test _check_python_file_is_safe tests for proper use of Text() and
        Html() for a Python file with a mix of rules.

        """
        linter = PythonLinter()
        results = FileResults('')

        file_content = textwrap.dedent("""
            msg1 = '<a href="{}"'.format(url)
            msg2 = "Mixed {link_start}text{link_end}".format(
                link_start=HTML("<a href='{}'>".format(url)),
                link_end="</a>",
            )
            msg3 = '<a href="%s"' % url
        """)

        linter.check_python_file_is_safe(file_content, results)

        results.violations.sort(key=lambda violation: violation.sort_key())

        self.assertEqual(len(results.violations), 5)
        self.assertEqual(results.violations[0].rule, Rules.python_wrap_html)
        self.assertEqual(results.violations[1].rule, Rules.python_requires_html_or_text)
        self.assertEqual(results.violations[2].rule, Rules.python_close_before_format)
        self.assertEqual(results.violations[3].rule, Rules.python_wrap_html)
        self.assertEqual(results.violations[4].rule, Rules.python_interpolate_html)

    @data(
        {
            'python':
                """
                    response_str = textwrap.dedent('''
                        <div>
                            <h3 class="result">{response}</h3>
                        </div>
                    ''').format(response=response_text)
                """,
            'rule': Rules.python_wrap_html,
            'start_line': 2,
        },
        {
            'python':
                """
                def function(self):
                    '''
                    Function comment.
                    '''
                    response_str = textwrap.dedent('''
                        <div>
                            <h3 class="result">{response}</h3>
                        </div>
                    ''').format(response=response_text)
                """,
            'rule': Rules.python_wrap_html,
            'start_line': 6,
        },
        {
            'python':
                """
                def function(self):
                    '''
                    Function comment.
                    '''
                    response_str = '''<h3 class="result">{response}</h3>'''.format(response=response_text)
                """,
            'rule': Rules.python_wrap_html,
            'start_line': 6,
        },
        {
            'python':
                """
                def function(self):
                    '''
                    Function comment.
                    '''
                    response_str = textwrap.dedent('''
                        <div>
                            \"\"\" Do we care about a nested triple quote? \"\"\"
                            <h3 class="result">{response}</h3>
                        </div>
                    ''').format(response=response_text)
                """,
            'rule': Rules.python_wrap_html,
            'start_line': 6,
        },
    )
    def test_check_python_with_triple_quotes(self, data):
        """
        Test _check_python_file_is_safe with triple quotes.

        """
        linter = PythonLinter()
        results = FileResults('')

        file_content = textwrap.dedent(data['python'])

        linter.check_python_file_is_safe(file_content, results)

        self._validate_data_rules(data, results)
        self.assertEqual(results.violations[0].start_line, data['start_line'])
