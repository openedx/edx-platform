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
    _process_os_walk, FileResults, MakoTemplateLinter, ParseString, UnderscoreTemplateLinter, Rules
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

    @data(
        {'expression': '${x}', 'rule': None},
        {'expression': '${{unbalanced}', 'rule': Rules.mako_unparseable_expression},
        {'expression': '${x | n}', 'rule': Rules.mako_invalid_html_filter},
        {'expression': '${x | n, unicode}', 'rule': None},
        {'expression': '${x | h}', 'rule': Rules.mako_unwanted_html_filter},
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

        self._validate_data_rule(data, results)

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

    @data(
        {
            'expression':
                textwrap.dedent("""
                    ${"Mixed {span_start}text{span_end}".format(
                        span_start=HTML("<span>"),
                        span_end=HTML("</span>"),
                    )}
                """),
            'rule': Rules.mako_html_requires_text
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
            'rule': Rules.mako_html_requires_text
        },
        {
            'expression':
                textwrap.dedent("""
                    ${Text("Mixed {link_start}text{link_end}".format(
                        link_start=HTML("<a href='{}'>").format(url),
                        link_end=HTML("</a>"),
                    ))}
                """),
            'rule': Rules.mako_close_before_format
        },
        {
            'expression':
                textwrap.dedent("""
                    ${Text("Mixed {link_start}text{link_end}").format(
                        link_start=HTML("<a href='{}'>".format(url)),
                        link_end=HTML("</a>"),
                    )}
                """),
            'rule': Rules.mako_close_before_format
        },
        {
            'expression':
                textwrap.dedent("""
                    ${"Mixed {span_start}text{span_end}".format(
                        span_start="<span>",
                        span_end="</span>",
                    )}
                """),
            'rule': Rules.mako_wrap_html
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
            'rule': Rules.mako_wrap_html
        },
        {
            'expression': "${'Embedded HTML <strong></strong>'}",
            'rule': Rules.mako_wrap_html
        },
        {
            'expression': "${ Text('text') }",
            'rule': Rules.mako_text_redundant
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
            'expression': "${ HTML('<span></span>') + 'some other text' }",
            'rule': Rules.mako_html_alone
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

        self._validate_data_rule(data, results)

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
        {'expression': '${x | n, unicode}', 'rule': None},
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
            <script>
                {expression}
            </script>
        """.format(expression=data['expression']))

        linter._check_mako_file_is_safe(mako_template, results)

        self._validate_data_rule(data, results)

    @data(
        {'expression': '${x}', 'rule': Rules.mako_invalid_js_filter},
        {'expression': '${x | n, js_escaped_string}', 'rule': None},
    )
    def test_check_mako_expressions_in_require_js(self, data):
        """
        Test _check_mako_file_is_safe in JavaScript require context provides
        appropriate violations
        """
        linter = MakoTemplateLinter()
        results = FileResults('')

        mako_template = textwrap.dedent("""
            <%page expression_filter="h"/>
            <%static:require_module module_name="${{x}}" class_name="TestFactory">
                {expression}
            </%static:require_module>
        """.format(expression=data['expression']))

        linter._check_mako_file_is_safe(mako_template, results)

        self._validate_data_rule(data, results)

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
        start_index = expressions[0]['start_index']
        end_index = expressions[0]['end_index']
        self.assertEqual(data['template'][start_index:end_index], data['template'].strip())
        self.assertEqual(expressions[0]['expression'], data['template'].strip())

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
        self.assertEqual(expressions[0]['start_index'], data['start_index'])
        self.assertIsNone(expressions[0]['expression'])

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
        self.assertEqual(data['template'][parse_string.start_index:parse_string.end_index], parse_string.string)
        start_index = parse_string.start_index + parse_string.quote_length
        end_index = parse_string.end_index - parse_string.quote_length
        self.assertEqual(data['template'][start_index:end_index], parse_string.string_inner)

    def _validate_data_rule(self, data, results):
        if data['rule'] is None:
            self.assertEqual(len(results.violations), 0)
        else:
            self.assertEqual(len(results.violations), 1)
            self.assertEqual(results.violations[0].rule, data['rule'])


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
