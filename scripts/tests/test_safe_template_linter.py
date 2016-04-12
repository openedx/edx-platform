"""
Tests for safe_template_linter.py
"""
from ddt import ddt, data
import mock
import re
from StringIO import StringIO
import textwrap
from unittest import TestCase

from ..safe_template_linter import (
    _process_os_walk, FileResults, MakoTemplateLinter, UnderscoreTemplateLinter, Rules
)


class TestSafeTemplateLinter(TestCase):
    """
    Test some top-level linter functions
    """

    def test_process_os_walk_with_includes(self):
        """
        Tests the top-level processing of template files, including Mako
        includes.
        """
        out = StringIO()

        options = {
            'is_quiet': False,
        }

        template_linters = [MakoTemplateLinter(), UnderscoreTemplateLinter()]

        with mock.patch.object(MakoTemplateLinter, '_is_valid_directory', return_value=True) as mock_is_valid_directory:
            _process_os_walk('scripts/tests/templates', template_linters, options, out)

        output = out.getvalue()
        self.assertIsNotNone(re.search('test\.html.*mako-missing-default', out.getvalue()))


@ddt
class TestMakoTemplateLinter(TestCase):
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
            'violations': 0,
            'rule': None
        },
        {
            'template':
                '\n <%page args="section_data" expression_filter="h" /> ',
            'violations': 0,
            'rule': None
        },
        {
            'template':
                '\n <%page expression_filter="h" /> '
                '\n <%page args="section_data"/>',
            'violations': 1,
            'rule': Rules.mako_multiple_page_tags
        },
        {
            'template': '\n <%page args="section_data" /> ',
            'violations': 1,
            'rule': Rules.mako_missing_default
        },
        {
            'template':
                '\n <%page args="section_data"/> <some-other-tag expression_filter="h" /> ',
            'violations': 1,
            'rule': Rules.mako_missing_default
        },
        {
            'template': '\n',
            'violations': 1,
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

        self.assertEqual(len(results.violations), data['violations'])
        if data['violations'] > 0:
            self.assertEqual(results.violations[0].rule, data['rule'])

    def test_check_mako_expressions_in_html(self):
        """
        Test _check_mako_file_is_safe in html context provides appropriate violations
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            ${x}
            ${'{{unbalanced-nested'}
            ${x | n}
            ${x | h}
            ${x | n, dump_js_escaped_json}
        """)

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), 4)
        self.assertEqual(results.violations[0].rule, Rules.mako_unparsable_expression)
        start_index = results.violations[0].expression['start_index']
        self.assertEqual(mako_template[start_index:start_index + 24], "${'{{unbalanced-nested'}")
        self.assertEqual(results.violations[1].rule, Rules.mako_invalid_html_filter)
        self.assertEqual(results.violations[1].expression['expression'], "${x | n}")
        self.assertEqual(results.violations[2].rule, Rules.mako_unwanted_html_filter)
        self.assertEqual(results.violations[2].expression['expression'], "${x | h}")
        self.assertEqual(results.violations[3].rule, Rules.mako_invalid_html_filter)
        self.assertEqual(results.violations[3].expression['expression'], "${x | n, dump_js_escaped_json}")

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
        self.assertEqual(results.violations[0].rule, Rules.mako_deprecated_display_name)

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

    def test_check_mako_expressions_in_javascript(self):
        """
        Test _check_mako_file_is_safe in JavaScript script context provides
        appropriate violations
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            <script>
                ${x}
                ${'{{unbalanced-nested'}
                ${x | n}
                ${x | h}
                ${x | n, dump_js_escaped_json}
                "${x-with-quotes | n, js_escaped_string}"
            </script>
        """)

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), 4)
        self.assertEqual(results.violations[0].rule, Rules.mako_invalid_js_filter)
        self.assertEqual(results.violations[0].expression['expression'], "${x}")
        self.assertEqual(results.violations[1].rule, Rules.mako_unparsable_expression)
        start_index = results.violations[1].expression['start_index']
        self.assertEqual(mako_template[start_index:start_index + 24], "${'{{unbalanced-nested'}")
        self.assertEqual(results.violations[2].rule, Rules.mako_invalid_js_filter)
        self.assertEqual(results.violations[2].expression['expression'], "${x | n}")
        self.assertEqual(results.violations[3].rule, Rules.mako_invalid_js_filter)
        self.assertEqual(results.violations[3].expression['expression'], "${x | h}")

    def test_check_mako_expressions_in_require_js(self):
        """
        Test _check_mako_file_is_safe in JavaScript require context provides
        appropriate violations
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            <%static:require_module module_name="${x}" class_name="TestFactory">
                ${x}
                ${x | n, js_escaped_string}
            </%static:require_module>
        """)

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), 1)
        self.assertEqual(results.violations[0].rule, Rules.mako_invalid_js_filter)
        self.assertEqual(results.violations[0].expression['expression'], "${x}")

    @data(
        {'media_type': 'text/javascript', 'expected_violations': 0},
        {'media_type': 'text/ecmascript', 'expected_violations': 0},
        {'media_type': 'application/ecmascript', 'expected_violations': 0},
        {'media_type': 'application/javascript', 'expected_violations': 0},
        {'media_type': 'text/template', 'expected_violations': 1},
        {'media_type': 'unknown/type', 'expected_violations': 1},
    )
    def test_check_mako_expressions_in_script_type(self, data):
        """
        Test _check_mako_file_is_safe in script tag with different media types
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            <script type="{}">
                ${{x | n, dump_js_escaped_json}}
            </script>
        """).format(data['media_type'])

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), data['expected_violations'])

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

    def test_expression_detailed_results(self):
        """
        Test _check_mako_file_is_safe provides detailed results, including line
        numbers, columns, and line
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            ${x | n}
                <div>${(
                    'tabbed-multi-line-expression'
                ) | n}</div>
            ${'{{unbalanced-nested' | n}
        """)

        linter._check_mako_file_is_safe(mako_template, results)

        self.assertEqual(len(results.violations), 4)
        self.assertEqual(results.violations[0].rule, Rules.mako_missing_default)

        self.assertEqual(results.violations[1].start_line, 2)
        self.assertEqual(results.violations[1].start_column, 1)
        self.assertEqual(results.violations[1].end_line, 2)
        self.assertEqual(results.violations[1].end_column, 8)
        self.assertEqual(len(results.violations[1].lines), 1)
        self.assertEqual(results.violations[1].lines[0], "${x | n}")

        self.assertEqual(results.violations[2].start_line, 3)
        self.assertEqual(results.violations[2].start_column, 10)
        self.assertEqual(results.violations[2].end_line, 5)
        self.assertEqual(results.violations[2].end_column, 10)
        self.assertEqual(len(results.violations[2].lines), 3)
        self.assertEqual(results.violations[2].lines[0], "    <div>${(")
        self.assertEqual(
            results.violations[2].lines[1],
            "        'tabbed-multi-line-expression'"
        )
        self.assertEqual(results.violations[2].lines[2], "    ) | n}</div>")

        self.assertEqual(results.violations[3].start_line, 6)
        self.assertEqual(results.violations[3].start_column, 1)
        self.assertEqual(results.violations[3].end_line, 6)
        self.assertEqual(results.violations[3].end_column, "?")
        self.assertEqual(len(results.violations[3].lines), 1)
        self.assertEqual(
            results.violations[3].lines[0],
            "${'{{unbalanced-nested' | n}"
        )

    def test_find_mako_expressions(self):
        """
        Test _find_mako_expressions finds appropriate expressions
        """
        linter = MakoTemplateLinter()

        mako_template = textwrap.dedent("""
            ${x}
                ${tabbed-x}
                ${(
                    'tabbed-multi-line-expression'
                )}
            ${'{{unbalanced-nested'}
            ${'{{nested}}'}
                <div>no expression</div>
        """)

        expressions = linter._find_mako_expressions(mako_template)

        self.assertEqual(len(expressions), 5)
        self._validate_expression(mako_template, expressions[0], '${x}')
        self._validate_expression(mako_template, expressions[1], '${tabbed-x}')
        self._validate_expression(mako_template, expressions[2], "${(\n        'tabbed-multi-line-expression'\n    )}")

        # won't parse unbalanced nested {}'s
        unbalanced_expression = "${'{{unbalanced-nested'}"
        self.assertEqual(expressions[3]['end_index'], -1)
        start_index = expressions[3]['start_index']
        self.assertEqual(mako_template[start_index:start_index + len(unbalanced_expression)], unbalanced_expression)
        self.assertEqual(expressions[3]['expression'], None)

        self._validate_expression(mako_template, expressions[4], "${'{{nested}}'}")

    def _validate_expression(self, template_string, expression, expected_expression):
        start_index = expression['start_index']
        end_index = expression['end_index']
        self.assertEqual(template_string[start_index:end_index + 1], expected_expression)
        self.assertEqual(expression['expression'], expected_expression)


@ddt
class TestUnderscoreTemplateLinter(TestCase):
    """
    Test UnderscoreTemplateLinter
    """

    def test_check_underscore_file_is_safe(self):
        """
        Test _check_underscore_file_is_safe with safe template
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        template = textwrap.dedent("""
            <%- gettext('Single Line') %>

            <%-
                gettext('Multiple Lines')
            %>
        """)

        linter._check_underscore_file_is_safe(template, results)

        self.assertEqual(len(results.violations), 0)

    def test_check_underscore_file_is_not_safe(self):
        """
        Test _check_underscore_file_is_safe with unsafe template
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        template = textwrap.dedent("""
            <%= gettext('Single Line') %>

            <%=
                gettext('Multiple Lines')
            %>
        """)

        linter._check_underscore_file_is_safe(template, results)

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
        Test _check_underscore_file_is_safe with various disabled pragmas
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        linter._check_underscore_file_is_safe(data['template'], results)

        violation_count = len(data['is_disabled'])
        self.assertEqual(len(results.violations), violation_count)
        for index in range(0, violation_count - 1):
            self.assertEqual(results.violations[index].is_disabled, data['is_disabled'][index])

    def test_check_underscore_file_disables_one_violation(self):
        """
        Test _check_underscore_file_is_safe with disabled before a line only
        disables for the violation following
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        template = textwrap.dedent("""
            <% // safe-lint: disable=underscore-not-escaped %>
            <%= message %>
            <%= message %>
        """)

        linter._check_underscore_file_is_safe(template, results)

        self.assertEqual(len(results.violations), 2)
        self.assertEqual(results.violations[0].is_disabled, True)
        self.assertEqual(results.violations[1].is_disabled, False)

    @data(
        {'template': '<%= HtmlUtils.ensureHtml(message) %>'},
        {'template': '<%= _.escape(message) %>'},
    )
    def test_check_underscore_no_escape_allowed(self, data):
        """
        Test _check_underscore_file_is_safe with expressions that are allowed
        without escaping because the internal calls properly escape.
        """
        linter = UnderscoreTemplateLinter()
        results = FileResults('')

        linter._check_underscore_file_is_safe(data['template'], results)

        self.assertEqual(len(results.violations), 0)
