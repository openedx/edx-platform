#!/usr/bin/env python
"""
A linting tool to check if templates are safe
"""
from __future__ import print_function
import argparse
from enum import Enum
import os
import re
import sys


class StringLines(object):
    """
    StringLines provides utility methods to work with a string in terms of
    lines.  As an example, it can convert an index into a line number or column
    number (i.e. index into the line).
    """

    def __init__(self, string):
        """
        Init method.

        Arguments:
            string: The string to work with.

        """
        self._string = string
        self._line_start_indexes = self._process_line_breaks(string)
        # this is an exclusive index used in the case that the template doesn't
        # end with a new line
        self.eof_index = len(string)

    def _process_line_breaks(self, string):
        """
        Creates a list, where each entry represents the index into the string
        where the next line break was found.

        Arguments:
            string: The string in which to find line breaks.

        Returns:
             A list of indices into the string at which each line begins.

        """
        line_start_indexes = [0]
        index = 0
        while True:
            index = string.find('\n', index)
            if index < 0:
                break
            index += 1
            line_start_indexes.append(index)
        return line_start_indexes

    def get_string(self):
        """
        Get the original string.
        """
        return self._string

    def index_to_line_number(self, index):
        """
        Given an index, determines the line of the index.

        Arguments:
            index: The index into the original string for which we want to know
                the line number

        Returns:
            The line number of the provided index.

        """
        current_line_number = 0
        for line_break_index in self._line_start_indexes:
            if line_break_index <= index:
                current_line_number += 1
            else:
                break
        return current_line_number

    def index_to_column_number(self, index):
        """
        Gets the column (i.e. index into the line) for the given index into the
        original string.

        Arguments:
            index: The index into the original string.

        Returns:
            The column (i.e. index into the line) for the given index into the
            original string.

        """
        start_index = self.index_to_line_start_index(index)
        column = index - start_index + 1
        return column

    def index_to_line_start_index(self, index):
        """
        Gets the index of the start of the line of the given index.

        Arguments:
            index: The index into the original string.

        Returns:
            The index of the start of the line of the given index.

        """
        line_number = self.index_to_line_number(index)
        return self.line_number_to_start_index(line_number)

    def index_to_line_end_index(self, index):
        """
        Gets the index of the end of the line of the given index.

        Arguments:
            index: The index into the original string.

        Returns:
            The index of the end of the line of the given index.

        """
        line_number = self.index_to_line_number(index)
        return self.line_number_to_end_index(line_number)

    def line_number_to_start_index(self, line_number):
        """
        Gets the starting index for the provided line number.

        Arguments:
            line_number: The line number of the line for which we want to find
                the start index.

        Returns:
            The starting index for the provided line number.

        """
        return self._line_start_indexes[line_number - 1]

    def line_number_to_end_index(self, line_number):
        """
        Gets the ending index for the provided line number.

        Arguments:
            line_number: The line number of the line for which we want to find
                the end index.

        Returns:
            The ending index for the provided line number.

        """
        if line_number < len(self._line_start_indexes):
            return self._line_start_indexes[line_number]
        else:
            # an exclusive index in the case that the file didn't end with a
            # newline.
            return self.eof_index

    def line_number_to_line(self, line_number):
        """
        Gets the line of text designated by the provided line number.

        Arguments:
            line_number: The line number of the line we want to find.

        Returns:
            The line of text designated by the provided line number.

        """
        start_index = self._line_start_indexes[line_number - 1]
        if len(self._line_start_indexes) == line_number:
            line = self._string[start_index:]
        else:
            end_index = self._line_start_indexes[line_number]
            line = self._string[start_index:end_index - 1]
        return line

    def line_count(self):
        """
        Gets the number of lines in the string.
        """
        return len(self._line_start_indexes)


class Rules(Enum):
    """
    An Enum of each rule which the linter will check.
    """
    mako_missing_default = (
        'mako-missing-default',
        'Missing default <%page expression_filter="h"/>.'
    )
    mako_multiple_page_tags = (
        'mako-multiple-page-tags',
        'A Mako template can only have one <%page> tag.'
    )
    mako_unparseable_expression = (
        'mako-unparseable-expression',
        'The expression could not be properly parsed.'
    )
    mako_unwanted_html_filter = (
        'mako-unwanted-html-filter',
        'Remove explicit h filters when it is provided by the page directive.'
    )
    mako_invalid_html_filter = (
        'mako-invalid-html-filter',
        'The expression is using an invalid filter in an HTML context.'
    )
    mako_invalid_js_filter = (
        'mako-invalid-js-filter',
        'The expression is using an invalid filter in a JavaScript context.'
    )
    mako_js_missing_quotes = (
        'mako-js-missing-quotes',
        'An expression using js_escaped_string must be wrapped in quotes.'
    )
    mako_js_html_string = (
        'mako-js-html-string',
        'A JavaScript string containing HTML should not have an embedded Mako expression.'
    )
    mako_html_requires_text = (
        'mako-html-requires-text',
        'You must begin with Text() if you use HTML() during interpolation.'
    )
    mako_text_redundant = (
        'mako-text-redundant',
        'Using Text() function without HTML() is unnecessary.'
    )
    mako_html_alone = (
        'mako-html-alone',
        "Only use HTML() alone with properly escaped HTML(), and make sure it is really alone."
    )
    mako_html_entities = (
        'mako-html-entities',
        "HTML entities should be plain text or wrapped with HTML()."
    )
    mako_unknown_context = (
        'mako-unknown-context',
        "The context could not be determined."
    )
    underscore_not_escaped = (
        'underscore-not-escaped',
        'Expressions should be escaped using <%- expression %>.'
    )
    javascript_jquery_append = (
        'javascript-jquery-append',
        'Use HtmlUtils.append() or .append(HtmlUtils.xxx().toString()).'
    )
    javascript_jquery_prepend = (
        'javascript-jquery-prepend',
        'Use HtmlUtils.prepend() or .prepend(HtmlUtils.xxx().toString()).'
    )
    javascript_jquery_insertion = (
        'javascript-jquery-insertion',
        'JQuery DOM insertion calls that take content must use HtmlUtils (e.g. $el.after(HtmlUtils.xxx().toString()).'
    )
    javascript_jquery_insert_into_target = (
        'javascript-jquery-insert-into-target',
        'JQuery DOM insertion calls that take a target can only be called from elements (e.g. .$el.appendTo()).'
    )
    javascript_jquery_html = (
        'javascript-jquery-html',
        "Use HtmlUtils.setHtml(), .html(HtmlUtils.xxx().toString()), or JQuery's text() function."
    )
    javascript_concat_html = (
        'javascript-concat-html',
        'Use HtmlUtils functions rather than concatenating strings with HTML.'
    )
    javascript_escape = (
        'javascript-escape',
        "Avoid calls to escape(), especially in Backbone. Use templates, HtmlUtils, or JQuery's text() function."
    )
    javascript_interpolate = (
        'javascript-interpolate',
        'Use StringUtils.interpolate() or HtmlUtils.interpolateHtml() as appropriate.'
    )
    python_concat_html = (
        'python-concat-html',
        'Use HTML() and Text() functions rather than concatenating strings with HTML.'
    )
    python_custom_escape = (
        'python-custom-escape',
        "Use markupsafe.escape() rather than custom escaping for '<'."
    )
    python_deprecated_display_name = (
        'python-deprecated-display-name',
        'Replace deprecated display_name_with_default_escaped with display_name_with_default.'
    )
    python_requires_html_or_text = (
        'python-requires-html-or-text',
        'You must start with Text() or HTML() if you use HTML() or Text() during interpolation.'
    )
    python_close_before_format = (
        'python-close-before-format',
        'You must close any call to Text() or HTML() before calling format().'
    )
    python_wrap_html = (
        'python-wrap-html',
        "String containing HTML should be wrapped with call to HTML()."
    )
    python_interpolate_html = (
        'python-interpolate-html',
        "Use HTML(), Text(), and format() functions for interpolating strings with HTML."
    )
    python_parse_error = (
        'python-parse-error',
        'Error parsing Python function or string.'
    )

    def __init__(self, rule_id, rule_summary):
        self.rule_id = rule_id
        self.rule_summary = rule_summary


class Expression(object):
    """
    Represents an arbitrary expression.

    An expression can be any type of code snippet. It will sometimes have a
    starting and ending delimiter, but not always.

    Here are some example expressions::

        ${x | n, decode.utf8}
        <%= x %>
        function(x)
        "<p>" + message + "</p>"

    Other details of note:
    - Only a start_index is required for a valid expression.
    - If end_index is None, it means we couldn't parse the rest of the
    expression.
    - All other details of the expression are optional, and are only added if
    and when supplied and needed for additional checks.  They are not necessary
    for the final results output.

    """

    def __init__(self, start_index, end_index=None, template=None, start_delim="", end_delim="", strings=None):
        """
        Init method.

        Arguments:
            start_index: the starting index of the expression
            end_index: the index immediately following the expression, or None
                if the expression was unparseable
            template: optional template code in which the expression was found
            start_delim: optional starting delimiter of the expression
            end_delim: optional ending delimeter of the expression
            strings: optional list of ParseStrings

        """
        self.start_index = start_index
        self.end_index = end_index
        self.start_delim = start_delim
        self.end_delim = end_delim
        self.strings = strings
        if template is not None and self.end_index is not None:
            self.expression = template[start_index:end_index]
            self.expression_inner = self.expression[len(start_delim):-len(end_delim)].strip()
        else:
            self.expression = None
            self.expression_inner = None


class RuleViolation(object):
    """
    Base class representing a rule violation which can be used for reporting.
    """

    def __init__(self, rule):
        """
        Init method.

        Arguments:
            rule: The Rule which was violated.

        """
        self.rule = rule
        self.full_path = ''
        self.is_disabled = False

    def _mark_disabled(self, string, scope_start_string=False):
        """
        Performs the disable pragma search and marks the rule as disabled if a
        matching pragma is found.

        Pragma format::

            safe-lint: disable=violation-name,other-violation-name

        Arguments:
            string: The string of code in which to search for the pragma.
            scope_start_string: True if the pragma must be at the start of the
                string, False otherwise. The pragma is considered at the start
                of the string if it has a maximum of 5 non-whitespace characters
                preceding it.

        Side Effect:
            Sets self.is_disabled as appropriate based on whether the pragma is
            found.

        """
        pragma_match = re.search(r'safe-lint:\s*disable=([a-zA-Z,-]+)', string)
        if pragma_match is None:
            return
        if scope_start_string:
            spaces_count = string.count(' ', 0, pragma_match.start())
            non_space_count = pragma_match.start() - spaces_count
            if non_space_count > 5:
                return

        for disabled_rule in pragma_match.group(1).split(','):
            if disabled_rule == self.rule.rule_id:
                self.is_disabled = True
                return

    def sort_key(self):
        """
        Returns a key that can be sorted on
        """
        return 0

    def first_line(self):
        """
        Since a file level rule has no first line, returns empty string.
        """
        return ''

    def prepare_results(self, full_path, string_lines):
        """
        Preps this instance for results reporting.

        Arguments:
            full_path: Path of the file in violation.
            string_lines: A StringLines containing the contents of the file in
                violation.

        """
        self.full_path = full_path
        self._mark_disabled(string_lines.get_string())

    def print_results(self, out):
        """
        Prints the results represented by this rule violation.

        Arguments:
            out: output file
        """
        print("{}: {}".format(self.full_path, self.rule.rule_id), file=out)


class ExpressionRuleViolation(RuleViolation):
    """
    A class representing a particular rule violation for expressions which
    contain more specific details of the location of the violation for reporting
    purposes.

    """

    def __init__(self, rule, expression):
        """
        Init method.

        Arguments:
            rule: The Rule which was violated.
            expression: The Expression that was in violation.

        """
        super(ExpressionRuleViolation, self).__init__(rule)
        self.expression = expression
        self.start_line = 0
        self.start_column = 0
        self.end_line = 0
        self.end_column = 0
        self.lines = []
        self.is_disabled = False

    def _mark_expression_disabled(self, string_lines):
        """
        Marks the expression violation as disabled if it finds the disable
        pragma anywhere on the first line of the violation, or at the start of
        the line preceding the violation.

        Pragma format::

            safe-lint: disable=violation-name,other-violation-name

        Examples::

            <% // safe-lint: disable=underscore-not-escaped %>
            <%= gettext('Single Line') %>

            <%= gettext('Single Line') %><% // safe-lint: disable=underscore-not-escaped %>

        Arguments:
            string_lines: A StringLines containing the contents of the file in
                violation.

        Side Effect:
            Sets self.is_disabled as appropriate based on whether the pragma is
            found.

        """
        # disable pragma can be at the start of the preceding line
        has_previous_line = self.start_line > 1
        if has_previous_line:
            line_to_check = string_lines.line_number_to_line(self.start_line - 1)
            self._mark_disabled(line_to_check, scope_start_string=True)
            if self.is_disabled:
                return

        # TODO: this should work at end of any line of the violation
        # disable pragma can be anywhere on the first line of the violation
        line_to_check = string_lines.line_number_to_line(self.start_line)
        self._mark_disabled(line_to_check, scope_start_string=False)

    def sort_key(self):
        """
        Returns a key that can be sorted on
        """
        return (self.start_line, self.start_column)

    def first_line(self):
        """
        Returns the initial line of code of the violation.
        """
        return self.lines[0]

    def prepare_results(self, full_path, string_lines):
        """
        Preps this instance for results reporting.

        Arguments:
            full_path: Path of the file in violation.
            string_lines: A StringLines containing the contents of the file in
                violation.

        """
        self.full_path = full_path
        start_index = self.expression.start_index
        self.start_line = string_lines.index_to_line_number(start_index)
        self.start_column = string_lines.index_to_column_number(start_index)
        end_index = self.expression.end_index
        if end_index is not None:
            self.end_line = string_lines.index_to_line_number(end_index)
            self.end_column = string_lines.index_to_column_number(end_index)
        else:
            self.end_line = self.start_line
            self.end_column = '?'
        for line_number in range(self.start_line, self.end_line + 1):
            self.lines.append(string_lines.line_number_to_line(line_number))
        self._mark_expression_disabled(string_lines)

    def print_results(self, out):
        """
        Prints the results represented by this rule violation.

        Arguments:
            out: output file

        """
        for line_number in range(self.start_line, self.end_line + 1):
            if line_number == self.start_line:
                column = self.start_column
                rule_id = self.rule.rule_id + ":"
            else:
                column = 1
                rule_id = " " * (len(self.rule.rule_id) + 1)
            print("{}: {}:{}: {} {}".format(
                self.full_path,
                line_number,
                column,
                rule_id,
                self.lines[line_number - self.start_line].encode(encoding='utf-8')
            ), file=out)


class FileResults(object):
    """
    Contains the results, or violations, for a file.
    """

    def __init__(self, full_path):
        """
        Init method.

        Arguments:
            full_path: The full path for this file.

        """
        self.full_path = full_path
        self.directory = os.path.dirname(full_path)
        self.is_file = os.path.isfile(full_path)
        self.violations = []

    def prepare_results(self, file_string, line_comment_delim=None):
        """
        Prepares the results for output for this file.

        Arguments:
            file_string: The string of content for this file.
            line_comment_delim: A string representing the start of a line
                comment. For example "##" for Mako and "//" for JavaScript.

        """
        string_lines = StringLines(file_string)
        for violation in self.violations:
            violation.prepare_results(self.full_path, string_lines)
        if line_comment_delim is not None:
            self._filter_commented_code(line_comment_delim)

    def print_results(self, options, out):
        """
        Prints the results (i.e. violations) in this file.

        Arguments:
            options: A list of the following options:
                list_files: True to print only file names, and False to print
                    all violations.
            out: output file

        Returns:
            The number of violations. When using --quiet, returns number of
            files with violations.

        """
        num_violations = 0
        if options['list_files']:
            if self.violations is not None and 0 < len(self.violations):
                num_violations += 1
                print(self.full_path, file=out)
        else:
            self.violations.sort(key=lambda violation: violation.sort_key())
            for violation in self.violations:
                if not violation.is_disabled:
                    num_violations += 1
                    violation.print_results(out)
        return num_violations

    def _filter_commented_code(self, line_comment_delim):
        """
        Remove any violations that were found in commented out code.

        Arguments:
            line_comment_delim: A string representing the start of a line
                comment. For example "##" for Mako and "//" for JavaScript.

        """
        self.violations = [v for v in self.violations if not self._is_commented(v, line_comment_delim)]

    def _is_commented(self, violation, line_comment_delim):
        """
        Checks if violation line is commented out.

        Arguments:
            violation: The violation to check
            line_comment_delim: A string representing the start of a line
                comment. For example "##" for Mako and "//" for JavaScript.

        Returns:
            True if the first line of the violation is actually commented out,
            False otherwise.
        """
        return violation.first_line().lstrip().startswith(line_comment_delim)


class ParseString(object):
    """
    ParseString is the result of parsing a string out of a template.

    A ParseString has the following attributes:
        start_index: The index of the first quote, or None if none found
        end_index: The index following the closing quote, or None if
            unparseable
        quote_length: The length of the quote.  Could be 3 for a Python
            triple quote.  Or None if none found.
        string: the text of the parsed string, or None if none found.
        string_inner: the text inside the quotes of the parsed string, or None
            if none found.

    """

    def __init__(self, template, start_index, end_index):
        """
        Init method.

        Arguments:
            template: The template to be searched.
            start_index: The start index to search.
            end_index: The end index to search before.

        """
        self.end_index = None
        self.quote_length = None
        self.string = None
        self.string_inner = None
        self.start_index = self._find_string_start(template, start_index, end_index)
        if self.start_index is not None:
            result = self._parse_string(template, self.start_index)
            if result is not None:
                self.end_index = result['end_index']
                self.quote_length = result['quote_length']
                self.string = result['string']
                self.string_inner = result['string_inner']

    def _find_string_start(self, template, start_index, end_index):
        """
        Finds the index of the end of start of a string.  In other words, the
        first single or double quote.

        Arguments:
            template: The template to be searched.
            start_index: The start index to search.
            end_index: The end index to search before.

        Returns:
            The start index of the first single or double quote, or None if no
            quote was found.
        """
        quote_regex = re.compile(r"""['"]""")
        start_match = quote_regex.search(template, start_index, end_index)
        if start_match is None:
            return None
        else:
            return start_match.start()

    def _parse_string(self, template, start_index):
        """
        Finds the indices of a string inside a template.

        Arguments:
            template: The template to be searched.
            start_index: The start index of the open quote.

        Returns:
            A dict containing the following, or None if not parseable:
                end_index: The index following the closing quote
                quote_length: The length of the quote.  Could be 3 for a Python
                    triple quote.
                string: the text of the parsed string
                string_inner: the text inside the quotes of the parsed string

        """
        quote = template[start_index]
        if quote not in ["'", '"']:
            raise ValueError("start_index must refer to a single or double quote.")
        triple_quote = quote * 3
        if template.startswith(triple_quote, start_index):
            quote = triple_quote

        next_start_index = start_index + len(quote)
        while True:
            quote_end_index = template.find(quote, next_start_index)
            backslash_index = template.find("\\", next_start_index)
            if quote_end_index < 0:
                return None
            if 0 <= backslash_index < quote_end_index:
                next_start_index = backslash_index + 2
            else:
                end_index = quote_end_index + len(quote)
                quote_length = len(quote)
                string = template[start_index:end_index]
                return {
                    'end_index': end_index,
                    'quote_length': quote_length,
                    'string': string,
                    'string_inner': string[quote_length:-quote_length],
                }


class BaseLinter(object):
    """
    BaseLinter provides some helper functions that are used by multiple linters.

    """
    def __init__(self):
        """
        Init method.
        """
        self._skip_dirs = (
            '.pycharm_helpers',
            'common/static/xmodule/modules',
            'node_modules',
            'reports/diff_quality',
            'spec',
            'scripts/tests/templates',
            'test_root',
            'vendor',
            'perf_tests'
        )

    def _is_skip_dir(self, skip_dirs, directory):
        """
        Determines whether a directory should be skipped or linted.

        Arguments:
            skip_dirs: The configured directories to be skipped.
            directory: The current directory to be tested.

        Returns:
             True if the directory should be skipped, and False otherwise.

        """
        for skip_dir in skip_dirs:
            skip_dir_regex = re.compile("(.*/)*{}(/.*)*".format(skip_dir))
            if skip_dir_regex.match(directory) is not None:
                return True
        return False

    def _is_valid_directory(self, skip_dirs, directory):
        """
        Determines if the provided directory is a directory that could contain
        a file that needs to be linted.

        Arguments:
            skip_dirs: The directories to be skipped.
            directory: The directory to be linted.

        Returns:
            True if this directory should be linted for violations and False
            otherwise.
        """
        if self._is_skip_dir(skip_dirs, directory):
            return False

        return True

    def _load_file(self, file_full_path):
        """
        Loads a file into a string.

        Arguments:
            file_full_path: The full path of the file to be loaded.

        Returns:
            A string containing the files contents.

        """
        with open(file_full_path, 'r') as input_file:
            file_contents = input_file.read()
            return file_contents.decode(encoding='utf-8')

    def _load_and_check_file_is_safe(self, file_full_path, lint_function, results):
        """
        Loads the Python file and checks if it is in violation.

        Arguments:
            file_full_path: The file to be loaded and linted.
            lint_function: A function that will lint for violations. It must
                take two arguments:
                1) string contents of the file
                2) results object
            results: A FileResults to be used for this file

        Returns:
            The file results containing any violations.

        """
        file_contents = self._load_file(file_full_path)
        lint_function(file_contents, results)
        return results

    def _find_closing_char_index(
            self, start_delim, open_char, close_char, template, start_index, num_open_chars=0, strings=None
    ):
        """
        Finds the index of the closing char that matches the opening char.

        For example, this could be used to find the end of a Mako expression,
        where the open and close characters would be '{' and '}'.

        Arguments:
            start_delim: If provided (e.g. '${' for Mako expressions), the
                closing character must be found before the next start_delim.
            open_char: The opening character to be matched (e.g '{')
            close_char: The closing character to be matched (e.g '}')
            template: The template to be searched.
            start_index: The start index of the last open char.
            num_open_chars: The current number of open chars.
            strings: A list of ParseStrings already parsed

        Returns:
            A dict containing the following, or None if unparseable:
                close_char_index: The index of the closing character
                strings: a list of ParseStrings

        """
        strings = [] if strings is None else strings
        close_char_index = template.find(close_char, start_index)
        if close_char_index < 0:
            # if we can't find a close char, let's just quit
            return None
        open_char_index = template.find(open_char, start_index, close_char_index)
        parse_string = ParseString(template, start_index, close_char_index)

        valid_index_list = [close_char_index]
        if 0 <= open_char_index:
            valid_index_list.append(open_char_index)
        if parse_string.start_index is not None:
            valid_index_list.append(parse_string.start_index)
        min_valid_index = min(valid_index_list)

        if parse_string.start_index == min_valid_index:
            strings.append(parse_string)
            if parse_string.end_index is None:
                return None
            else:
                return self._find_closing_char_index(
                    start_delim, open_char, close_char, template, start_index=parse_string.end_index,
                    num_open_chars=num_open_chars, strings=strings
                )

        if open_char_index == min_valid_index:
            if start_delim is not None:
                # if we find another starting delim, consider this unparseable
                start_delim_index = template.find(start_delim, start_index, close_char_index)
                if 0 <= start_delim_index < open_char_index:
                    return None
            return self._find_closing_char_index(
                start_delim, open_char, close_char, template, start_index=open_char_index + 1,
                num_open_chars=num_open_chars + 1, strings=strings
            )

        if num_open_chars == 0:
            return {
                'close_char_index': close_char_index,
                'strings': strings,
            }
        else:
            return self._find_closing_char_index(
                start_delim, open_char, close_char, template, start_index=close_char_index + 1,
                num_open_chars=num_open_chars - 1, strings=strings
            )

    def _check_concat_with_html(self, file_contents, rule, results):
        """
        Checks that strings with HTML are not concatenated

        Arguments:
            file_contents: The contents of the JavaScript file.
            rule: The rule that was violated if this fails.
            results: A file results objects to which violations will be added.

        """
        lines = StringLines(file_contents)
        last_expression = None
        # attempt to match a string that starts with '<' or ends with '>'
        regex_string_with_html = r"""["'](?:\s*<.*|.*>\s*)["']"""
        regex_concat_with_html = r"(\+\s*{}|{}\s*\+)".format(regex_string_with_html, regex_string_with_html)
        for match in re.finditer(regex_concat_with_html, file_contents):
            found_new_violation = False
            if last_expression is not None:
                last_line = lines.index_to_line_number(last_expression.start_index)
                # check if violation should be expanded to more of the same line
                if last_line == lines.index_to_line_number(match.start()):
                    last_expression = Expression(
                        last_expression.start_index, match.end(), template=file_contents
                    )
                else:
                    results.violations.append(ExpressionRuleViolation(
                        rule, last_expression
                    ))
                    found_new_violation = True
            else:
                found_new_violation = True
            if found_new_violation:
                last_expression = Expression(
                    match.start(), match.end(), template=file_contents
                )

        # add final expression
        if last_expression is not None:
            results.violations.append(ExpressionRuleViolation(
                rule, last_expression
            ))


class UnderscoreTemplateLinter(BaseLinter):
    """
    The linter for Underscore.js template files.
    """
    def __init__(self):
        """
        Init method.
        """
        super(UnderscoreTemplateLinter, self).__init__()
        self._skip_underscore_dirs = self._skip_dirs + ('test',)

    def process_file(self, directory, file_name):
        """
        Process file to determine if it is an Underscore template file and
        if it is safe.

        Arguments:
            directory (string): The directory of the file to be checked
            file_name (string): A filename for a potential underscore file

        Returns:
            The file results containing any violations.

        """
        full_path = os.path.normpath(directory + '/' + file_name)
        results = FileResults(full_path)

        if not self._is_valid_directory(self._skip_underscore_dirs, directory):
            return results

        if not file_name.lower().endswith('.underscore'):
            return results

        return self._load_and_check_file_is_safe(full_path, self.check_underscore_file_is_safe, results)

    def check_underscore_file_is_safe(self, underscore_template, results):
        """
        Checks for violations in an Underscore.js template.

        Arguments:
            underscore_template: The contents of the Underscore.js template.
            results: A file results objects to which violations will be added.

        """
        self._check_underscore_expressions(underscore_template, results)
        results.prepare_results(underscore_template)

    def _check_underscore_expressions(self, underscore_template, results):
        """
        Searches for Underscore.js expressions that contain violations.

        Arguments:
            underscore_template: The contents of the Underscore.js template.
            results: A list of results into which violations will be added.

        """
        expressions = self._find_unescaped_expressions(underscore_template)
        for expression in expressions:
            if not self._is_safe_unescaped_expression(expression):
                results.violations.append(ExpressionRuleViolation(
                    Rules.underscore_not_escaped, expression
                ))

    def _is_safe_unescaped_expression(self, expression):
        """
        Determines whether an expression is safely escaped, even though it is
        using the expression syntax that doesn't itself escape (i.e. <%= ).

        In some cases it is ok to not use the Underscore.js template escape
        (i.e. <%- ) because the escaping is happening inside the expression.

        Safe examples::

            <%= HtmlUtils.ensureHtml(message) %>
            <%= _.escape(message) %>

        Arguments:
            expression: The Expression being checked.

        Returns:
            True if the Expression has been safely escaped, and False otherwise.

        """
        if expression.expression_inner.startswith('HtmlUtils.'):
            return True
        if expression.expression_inner.startswith('_.escape('):
            return True
        return False

    def _find_unescaped_expressions(self, underscore_template):
        """
        Returns a list of unsafe expressions.

        At this time all expressions that are unescaped are considered unsafe.

        Arguments:
            underscore_template: The contents of the Underscore.js template.

        Returns:
            A list of Expressions.
        """
        unescaped_expression_regex = re.compile("<%=.*?%>", re.DOTALL)

        expressions = []
        for match in unescaped_expression_regex.finditer(underscore_template):
            expression = Expression(
                match.start(), match.end(), template=underscore_template, start_delim="<%=", end_delim="%>"
            )
            expressions.append(expression)
        return expressions


class JavaScriptLinter(BaseLinter):
    """
    The linter for JavaScript and CoffeeScript files.
    """
    underScoreLinter = UnderscoreTemplateLinter()

    def __init__(self):
        """
        Init method.
        """
        super(JavaScriptLinter, self).__init__()
        self._skip_javascript_dirs = self._skip_dirs + ('i18n', 'static/coffee')
        self._skip_coffeescript_dirs = self._skip_dirs

    def process_file(self, directory, file_name):
        """
        Process file to determine if it is a JavaScript file and
        if it is safe.

        Arguments:
            directory (string): The directory of the file to be checked
            file_name (string): A filename for a potential JavaScript file

        Returns:
            The file results containing any violations.

        """
        file_full_path = os.path.normpath(directory + '/' + file_name)
        results = FileResults(file_full_path)

        if not results.is_file:
            return results

        if file_name.lower().endswith('.js') and not file_name.lower().endswith('.min.js'):
            skip_dirs = self._skip_javascript_dirs
        elif file_name.lower().endswith('.coffee'):
            skip_dirs = self._skip_coffeescript_dirs
        else:
            return results

        if not self._is_valid_directory(skip_dirs, directory):
            return results

        return self._load_and_check_file_is_safe(file_full_path, self.check_javascript_file_is_safe, results)

    def check_javascript_file_is_safe(self, file_contents, results):
        """
        Checks for violations in a JavaScript file.

        Arguments:
            file_contents: The contents of the JavaScript file.
            results: A file results objects to which violations will be added.

        """
        no_caller_check = None
        no_argument_check = None
        self._check_jquery_function(
            file_contents, "append", Rules.javascript_jquery_append, no_caller_check,
            self._is_jquery_argument_safe, results
        )
        self._check_jquery_function(
            file_contents, "prepend", Rules.javascript_jquery_prepend, no_caller_check,
            self._is_jquery_argument_safe, results
        )
        self._check_jquery_function(
            file_contents, "unwrap|wrap|wrapAll|wrapInner|after|before|replaceAll|replaceWith",
            Rules.javascript_jquery_insertion, no_caller_check, self._is_jquery_argument_safe, results
        )
        self._check_jquery_function(
            file_contents, "appendTo|prependTo|insertAfter|insertBefore",
            Rules.javascript_jquery_insert_into_target, self._is_jquery_insert_caller_safe, no_argument_check, results
        )
        self._check_jquery_function(
            file_contents, "html", Rules.javascript_jquery_html, no_caller_check,
            self._is_jquery_html_argument_safe, results
        )
        self._check_javascript_interpolate(file_contents, results)
        self._check_javascript_escape(file_contents, results)
        self._check_concat_with_html(file_contents, Rules.javascript_concat_html, results)
        self.underScoreLinter.check_underscore_file_is_safe(file_contents, results)
        results.prepare_results(file_contents, line_comment_delim='//')

    def _get_expression_for_function(self, file_contents, function_start_match):
        """
        Returns an expression that matches the function call opened with
        function_start_match.

        Arguments:
            file_contents: The contents of the JavaScript file.
            function_start_match: A regex match representing the start of the function
                call (e.g. ".escape(").

        Returns:
            An Expression that best matches the function.

        """
        start_index = function_start_match.start()
        inner_start_index = function_start_match.end()
        result = self._find_closing_char_index(
            None, "(", ")", file_contents, start_index=inner_start_index
        )
        if result is not None:
            end_index = result['close_char_index'] + 1
            expression = Expression(
                start_index, end_index, template=file_contents, start_delim=function_start_match.group(), end_delim=")"
            )
        else:
            expression = Expression(start_index)
        return expression

    def _check_javascript_interpolate(self, file_contents, results):
        """
        Checks that interpolate() calls are safe.

        Only use of StringUtils.interpolate() or HtmlUtils.interpolateText()
        are safe.

        Arguments:
            file_contents: The contents of the JavaScript file.
            results: A file results objects to which violations will be added.

        """
        # Ignores calls starting with "StringUtils.", because those are safe
        regex = re.compile(r"(?<!StringUtils).interpolate\(")
        for function_match in regex.finditer(file_contents):
            expression = self._get_expression_for_function(file_contents, function_match)
            results.violations.append(ExpressionRuleViolation(Rules.javascript_interpolate, expression))

    def _check_javascript_escape(self, file_contents, results):
        """
        Checks that only necessary escape() are used.

        Allows for _.escape(), although this shouldn't be the recommendation.

        Arguments:
            file_contents: The contents of the JavaScript file.
            results: A file results objects to which violations will be added.

        """
        # Ignores calls starting with "_.", because those are safe
        regex = regex = re.compile(r"(?<!_).escape\(")
        for function_match in regex.finditer(file_contents):
            expression = self._get_expression_for_function(file_contents, function_match)
            results.violations.append(ExpressionRuleViolation(Rules.javascript_escape, expression))

    def _check_jquery_function(self, file_contents, function_names, rule, is_caller_safe, is_argument_safe, results):
        """
        Checks that the JQuery function_names (e.g. append(), prepend()) calls
        are safe.

        Arguments:
            file_contents: The contents of the JavaScript file.
            function_names: A pipe delimited list of names of the functions
                (e.g. "wrap|after|before").
            rule: The name of the rule to use for validation errors (e.g.
                Rules.javascript_jquery_append).
            is_caller_safe: A function to test if caller of the JQuery function
                is safe.
            is_argument_safe: A function to test if the argument passed to the
                JQuery function is safe.
            results: A file results objects to which violations will be added.

        """
        # Ignores calls starting with "HtmlUtils.", because those are safe
        regex = re.compile(r"(?<!HtmlUtils).(?:{})\(".format(function_names))
        for function_match in regex.finditer(file_contents):
            is_violation = True
            expression = self._get_expression_for_function(file_contents, function_match)
            if expression.end_index is not None:
                start_index = expression.start_index
                inner_start_index = function_match.end()
                close_paren_index = expression.end_index - 1
                function_argument = file_contents[inner_start_index:close_paren_index].strip()
                if is_argument_safe is not None and is_caller_safe is None:
                    is_violation = is_argument_safe(function_argument) is False
                elif is_caller_safe is not None and is_argument_safe is None:
                    line_start_index = StringLines(file_contents).index_to_line_start_index(start_index)
                    caller_line_start = file_contents[line_start_index:start_index]
                    is_violation = is_caller_safe(caller_line_start) is False
                else:
                    raise ValueError("Must supply either is_argument_safe, or is_caller_safe, but not both.")
            if is_violation:
                results.violations.append(ExpressionRuleViolation(rule, expression))

    def _is_jquery_argument_safe_html_utils_call(self, argument):
        """
        Checks that the argument sent to a jQuery DOM insertion function is a
        safe call to HtmlUtils.

        A safe argument is of the form:
        - HtmlUtils.xxx(anything).toString()
        - edx.HtmlUtils.xxx(anything).toString()

        Arguments:
            argument: The argument sent to the jQuery function (e.g.
            append(argument)).

        Returns:
            True if the argument is safe, and False otherwise.

        """
        # match on HtmlUtils.xxx().toString() or edx.HtmlUtils
        match = re.search(r"(?:edx\.)?HtmlUtils\.[a-zA-Z0-9]+\(.*\)\.toString\(\)", argument)
        return match is not None and match.group() == argument

    def _is_jquery_argument_safe(self, argument):
        """
        Check the argument sent to a jQuery DOM insertion function (e.g.
        append()) to check if it is safe.

        Safe arguments include:
        - the argument can end with ".el", ".$el" (with no concatenation)
        - the argument can be a single variable ending in "El" or starting with
            "$". For example, "testEl" or "$test".
        - the argument can be a single string literal with no HTML tags
        - the argument can be a call to $() with the first argument a string
            literal with a single HTML tag.  For example, ".append($('<br/>'))"
            or ".append($('<br/>'))".
        - the argument can be a call to HtmlUtils.xxx(html).toString()

        Arguments:
            argument: The argument sent to the jQuery function (e.g.
            append(argument)).

        Returns:
            True if the argument is safe, and False otherwise.

        """
        match_variable_name = re.search("[_$a-zA-Z]+[_$a-zA-Z0-9]*", argument)
        if match_variable_name is not None and match_variable_name.group() == argument:
            if argument.endswith('El') or argument.startswith('$'):
                return True
        elif argument.startswith('"') or argument.startswith("'"):
            # a single literal string with no HTML is ok
            # 1. it gets rid of false negatives for non-jquery calls (e.g. graph.append("g"))
            # 2. JQuery will treat this as a plain text string and will escape any & if needed.
            string = ParseString(argument, 0, len(argument))
            if string.string == argument and "<" not in argument:
                return True
        elif argument.startswith('$('):
            # match on JQuery calls with single string and single HTML tag
            # Examples:
            #    $("<span>")
            #    $("<div/>")
            #    $("<div/>", {...})
            match = re.search(r"""\$\(\s*['"]<[a-zA-Z0-9]+\s*[/]?>['"]\s*[,)]""", argument)
            if match is not None:
                return True
        elif self._is_jquery_argument_safe_html_utils_call(argument):
            return True
        # check rules that shouldn't use concatenation
        elif "+" not in argument:
            if argument.endswith('.el') or argument.endswith('.$el'):
                return True
        return False

    def _is_jquery_html_argument_safe(self, argument):
        """
        Check the argument sent to the jQuery html() function to check if it is
        safe.

        Safe arguments to html():
        - no argument (i.e. getter rather than setter)
        - empty string is safe
        - the argument can be a call to HtmlUtils.xxx(html).toString()

        Arguments:
            argument: The argument sent to html() in code (i.e. html(argument)).

        Returns:
            True if the argument is safe, and False otherwise.

        """
        if argument == "" or argument == "''" or argument == '""':
            return True
        elif self._is_jquery_argument_safe_html_utils_call(argument):
            return True
        return False

    def _is_jquery_insert_caller_safe(self, caller_line_start):
        """
        Check that the caller of a jQuery DOM insertion function that takes a
        target is safe (e.g. thisEl.appendTo(target)).

        If original line was::

            draggableObj.iconEl.appendTo(draggableObj.containerEl);

        Parameter caller_line_start would be:

            draggableObj.iconEl

        Safe callers include:
        - the caller can be ".el", ".$el"
        - the caller can be a single variable ending in "El" or starting with
            "$". For example, "testEl" or "$test".

        Arguments:
            caller_line_start: The line leading up to the jQuery function call.

        Returns:
            True if the caller is safe, and False otherwise.

        """
        # matches end of line for caller, which can't itself be a function
        caller_match = re.search(r"(?:\s*|[.])([_$a-zA-Z]+[_$a-zA-Z0-9])*$", caller_line_start)
        if caller_match is None:
            return False
        caller = caller_match.group(1)
        if caller is None:
            return False
        elif caller.endswith('El') or caller.startswith('$'):
            return True
        elif caller == 'el' or caller == 'parentNode':
            return True
        return False


class PythonLinter(BaseLinter):
    """
    The linter for Python files.

    The current implementation of the linter does naive Python parsing. It does
    not use the parser. One known issue is that parsing errors found inside a
    docstring need to be disabled, rather than being automatically skipped.
    Skipping docstrings is an enhancement that could be added.
    """

    def __init__(self):
        """
        Init method.
        """
        super(PythonLinter, self).__init__()
        self._skip_python_dirs = self._skip_dirs + ('tests', 'test/acceptance')

    def process_file(self, directory, file_name):
        """
        Process file to determine if it is a Python file and
        if it is safe.

        Arguments:
            directory (string): The directory of the file to be checked
            file_name (string): A filename for a potential Python file

        Returns:
            The file results containing any violations.

        """
        file_full_path = os.path.normpath(directory + '/' + file_name)
        results = FileResults(file_full_path)

        if not results.is_file:
            return results

        if file_name.lower().endswith('.py') is False:
            return results

        # skip this linter code (i.e. safe_template_linter.py)
        if file_name == os.path.basename(__file__):
            return results

        if not self._is_valid_directory(self._skip_python_dirs, directory):
            return results

        return self._load_and_check_file_is_safe(file_full_path, self.check_python_file_is_safe, results)

    def check_python_file_is_safe(self, file_contents, results):
        """
        Checks for violations in a Python file.

        Arguments:
            file_contents: The contents of the Python file.
            results: A file results objects to which violations will be added.

        """
        self._check_concat_with_html(file_contents, Rules.python_concat_html, results)
        self._check_deprecated_display_name(file_contents, results)
        self._check_custom_escape(file_contents, results)
        self._check_html(file_contents, results)
        results.prepare_results(file_contents, line_comment_delim='#')

    def _check_deprecated_display_name(self, file_contents, results):
        """
        Checks that the deprecated display_name_with_default_escaped is not
        used. Adds violation to results if there is a problem.

        Arguments:
            file_contents: The contents of the Python file
            results: A list of results into which violations will be added.

        """
        for match in re.finditer(r'\.display_name_with_default_escaped', file_contents):
            expression = Expression(match.start(), match.end())
            results.violations.append(ExpressionRuleViolation(
                Rules.python_deprecated_display_name, expression
            ))

    def _check_custom_escape(self, file_contents, results):
        """
        Checks for custom escaping calls, rather than using a standard escaping
        method.

        Arguments:
            file_contents: The contents of the Python file
            results: A list of results into which violations will be added.

        """
        for match in re.finditer("(<.*&lt;|&lt;.*<)", file_contents):
            expression = Expression(match.start(), match.end())
            results.violations.append(ExpressionRuleViolation(
                Rules.python_custom_escape, expression
            ))

    def _check_html(self, file_contents, results):
        """
        Checks many rules related to HTML in a Python file.

        Arguments:
            file_contents: The contents of the Python file
            results: A list of results into which violations will be added.

        """
        # Text() Expressions keyed by its end index
        text_calls_by_end_index = {}
        # HTML() Expressions keyed by its end index
        html_calls_by_end_index = {}
        start_index = 0
        while True:

            # check HTML(), Text() and format() calls
            result = self._check_html_text_format(
                file_contents, start_index, text_calls_by_end_index, html_calls_by_end_index, results
            )
            next_start_index = result['next_start_index']
            interpolate_end_index = result['interpolate_end_index']

            # check for interpolation including HTML outside of function calls
            self._check_interpolate_with_html(
                file_contents, start_index, interpolate_end_index, results
            )

            # advance the search
            start_index = next_start_index

            # end if there is nothing left to search
            if interpolate_end_index is None:
                break

    def _check_html_text_format(
            self, file_contents, start_index, text_calls_by_end_index, html_calls_by_end_index, results
    ):
        """
        Checks for HTML(), Text() and format() calls, and various rules related
        to these calls.

        Arguments:
            file_contents: The contents of the Python file
            start_index: The index at which to begin searching for a function
                call.
            text_calls_by_end_index: Text() Expressions keyed by its end index.
            html_calls_by_end_index: HTML() Expressions keyed by its end index.
            results: A list of results into which violations will be added.

        Returns:
            A dict with the following keys:
                'next_start_index': The start index of the next search for a
                    function call.
                'interpolate_end_index': The end index of the next next search
                    for interpolation with html, or None if the end of file
                    should be used.

        """
        # used to find opening of .format(), Text() and HTML() calls
        regex_function_open = re.compile(r"(\.format\(|(?<!\w)HTML\(|(?<!\w)Text\()")
        interpolate_end_index = None
        end_index = None
        strings = None
        html_calls = []
        while True:
            # first search for HTML(), Text(), or .format()
            if end_index is None:
                function_match = regex_function_open.search(file_contents, start_index)
            else:
                function_match = regex_function_open.search(file_contents, start_index, end_index)
            if function_match is not None:
                if interpolate_end_index is None:
                    interpolate_end_index = function_match.start()
                function_close_result = self._find_closing_char_index(
                    None, '(', ')', file_contents, start_index=function_match.end(),
                )
                if function_close_result is None:
                    results.violations.append(ExpressionRuleViolation(
                        Rules.python_parse_error, Expression(function_match.start())
                    ))
                else:
                    expression = Expression(
                        function_match.start(), function_close_result['close_char_index'] + 1, file_contents,
                        start_delim=function_match.group(), end_delim=")"
                    )
                    # if this an outer most Text(), HTML(), or format() call
                    if end_index is None:
                        end_index = expression.end_index
                        interpolate_end_index = expression.start_index
                        strings = function_close_result['strings']
                    if function_match.group() == '.format(':
                        if 'HTML(' in expression.expression_inner or 'Text(' in expression.expression_inner:
                            is_wrapped_with_text = str(function_match.start()) in text_calls_by_end_index.keys()
                            is_wrapped_with_html = str(function_match.start()) in html_calls_by_end_index.keys()
                            if is_wrapped_with_text is False and is_wrapped_with_html is False:
                                results.violations.append(ExpressionRuleViolation(
                                    Rules.python_requires_html_or_text, expression
                                ))
                    else:  # expression is 'HTML(' or 'Text('
                        # HTML() and Text() calls cannot contain any inner HTML(), Text(), or format() calls.
                        # Generally, format() would be the issue if there is one.
                        if regex_function_open.search(expression.expression_inner) is not None:
                            results.violations.append(ExpressionRuleViolation(
                                Rules.python_close_before_format, expression
                            ))
                        if function_match.group() == 'Text(':
                            text_calls_by_end_index[str(expression.end_index)] = expression
                        else:  # function_match.group() == 'HTML(':
                            html_calls_by_end_index[str(expression.end_index)] = expression
                            html_calls.append(expression)

                start_index = function_match.end()
            else:
                break

        # checks strings in the outer most call to ensure they are properly
        # wrapped with HTML()
        self._check_format_html_strings_wrapped(strings, html_calls, results)

        # compute where to continue the search
        if function_match is None and end_index is None:
            next_start_index = start_index
        elif end_index is None:
            next_start_index = function_match.end()
        else:
            next_start_index = end_index

        return {
            'next_start_index': next_start_index,
            'interpolate_end_index': interpolate_end_index,
        }

    def _check_format_html_strings_wrapped(self, strings, html_calls, results):
        """
        Checks that any string inside a format call that seems to contain HTML
        is wrapped with a call to HTML().

        Arguments:
            strings: A list of ParseStrings for each string inside the format()
                call.
            html_calls: A list of Expressions representing all of the HTML()
                calls inside the format() call.
            results: A list of results into which violations will be added.

        """
        html_strings = []
        html_wrapped_strings = []
        if strings is not None:
            # find all strings that contain HTML
            for string in strings:
                if '<' in string.string:
                    html_strings.append(string)
                    # check if HTML string is appropriately wrapped
                    for html_call in html_calls:
                        if html_call.start_index < string.start_index < string.end_index < html_call.end_index:
                            html_wrapped_strings.append(string)
                            break
            # loop through all unwrapped strings
            for unsafe_string in set(html_strings) - set(html_wrapped_strings):
                unsafe_string_expression = Expression(unsafe_string.start_index)
                results.violations.append(ExpressionRuleViolation(
                    Rules.python_wrap_html, unsafe_string_expression
                ))

    def _check_interpolate_with_html(self, file_contents, start_index, end_index, results):
        """
        Find interpolations with html that fall outside of any calls to HTML(),
        Text(), and .format().

        Arguments:
            file_contents: The contents of the Python file
            start_index: The index to start the search, or None if nothing to
                search
            end_index: The index to end the search, or None if the end of file
                should be used.
            results: A list of results into which violations will be added.

        """
        # used to find interpolation with HTML
        pattern_interpolate_html_inner = r'(<.*%s|%s.*<|<.*{\w*}|{\w*}.*<)'
        regex_interpolate_html = re.compile(r"""(".*{}.*"|'.*{}.*')""".format(
            pattern_interpolate_html_inner, pattern_interpolate_html_inner
        ))
        if end_index is None:
            interpolate_string_iter = regex_interpolate_html.finditer(file_contents, start_index)
        else:
            interpolate_string_iter = regex_interpolate_html.finditer(file_contents, start_index, end_index)
        for match_html_string in interpolate_string_iter:
            expression = Expression(match_html_string.start(), match_html_string.end())
            results.violations.append(ExpressionRuleViolation(
                Rules.python_interpolate_html, expression
            ))


class MakoTemplateLinter(BaseLinter):
    """
    The linter for Mako template files.
    """
    javaScriptLinter = JavaScriptLinter()

    def process_file(self, directory, file_name):
        """
        Process file to determine if it is a Mako template file and
        if it is safe.

        Arguments:
            directory (string): The directory of the file to be checked
            file_name (string): A filename for a potential Mako file

        Returns:
            The file results containing any violations.

        """
        mako_file_full_path = os.path.normpath(directory + '/' + file_name)
        results = FileResults(mako_file_full_path)

        if not results.is_file:
            return results

        if not self._is_valid_directory(directory):
            return results

        # TODO: When safe-by-default is turned on at the platform level, will we:
        # 1. Turn it on for .html only, or
        # 2. Turn it on for all files, and have different rulesets that have
        #    different rules of .xml, .html, .js, .txt Mako templates (e.g. use
        #    the n filter to turn off h for some of these)?
        # For now, we only check .html and .xml files
        if not (file_name.lower().endswith('.html') or file_name.lower().endswith('.xml')):
            return results

        return self._load_and_check_file_is_safe(mako_file_full_path, self._check_mako_file_is_safe, results)

    def _is_valid_directory(self, directory):
        """
        Determines if the provided directory is a directory that could contain
        Mako template files that need to be linted.

        Arguments:
            directory: The directory to be linted.

        Returns:
            True if this directory should be linted for Mako template violations
            and False otherwise.
        """
        if self._is_skip_dir(self._skip_dirs, directory):
            return False

        # TODO: This is an imperfect guess concerning the Mako template
        # directories. This needs to be reviewed before turning on safe by
        # default at the platform level.
        if ('/templates/' in directory) or directory.endswith('/templates'):
            return True

        return False

    def _check_mako_file_is_safe(self, mako_template, results):
        """
        Checks for violations in a Mako template.

        Arguments:
            mako_template: The contents of the Mako template.
            results: A file results objects to which violations will be added.

        """
        if self._is_django_template(mako_template):
            return
        has_page_default = self._has_page_default(mako_template, results)
        self._check_mako_expressions(mako_template, has_page_default, results)
        results.prepare_results(mako_template, line_comment_delim='##')

    def _is_django_template(self, mako_template):
        """
            Determines if the template is actually a Django template.

        Arguments:
            mako_template: The template code.

        Returns:
            True if this is really a Django template, and False otherwise.

        """
        if re.search('({%.*%})|({{.*}})', mako_template) is not None:
            return True
        return False

    def _get_page_tag_count(self, mako_template):
        """
        Determines the number of page expressions in the Mako template. Ignores
        page expressions that are commented out.

        Arguments:
            mako_template: The contents of the Mako template.

        Returns:
            The number of page expressions
        """
        count = len(re.findall('<%page ', mako_template, re.IGNORECASE))
        count_commented = len(re.findall(r'##\s+<%page ', mako_template, re.IGNORECASE))
        return max(0, count - count_commented)

    def _has_page_default(self, mako_template, results):
        """
        Checks if the Mako template contains the page expression marking it as
        safe by default.

        Arguments:
            mako_template: The contents of the Mako template.
            results: A list of results into which violations will be added.

        Side effect:
            Adds violations regarding page default if necessary

        Returns:
            True if the template has the page default, and False otherwise.

        """
        page_tag_count = self._get_page_tag_count(mako_template)
        # check if there are too many page expressions
        if 2 <= page_tag_count:
            results.violations.append(RuleViolation(Rules.mako_multiple_page_tags))
            return False
        # make sure there is exactly 1 page expression, excluding commented out
        # page expressions, before proceeding
        elif page_tag_count != 1:
            results.violations.append(RuleViolation(Rules.mako_missing_default))
            return False
        # check that safe by default (h filter) is turned on
        page_h_filter_regex = re.compile('<%page[^>]*expression_filter=(?:"h"|\'h\')[^>]*/>')
        page_match = page_h_filter_regex.search(mako_template)
        if not page_match:
            results.violations.append(RuleViolation(Rules.mako_missing_default))
        return page_match

    def _check_mako_expressions(self, mako_template, has_page_default, results):
        """
        Searches for Mako expressions and then checks if they contain
        violations, including checking JavaScript contexts for JavaScript
        violations.

        Arguments:
            mako_template: The contents of the Mako template.
            has_page_default: True if the page is marked as default, False
                otherwise.
            results: A list of results into which violations will be added.

        """
        expressions = self._find_mako_expressions(mako_template)
        contexts = self._get_contexts(mako_template)
        self._check_javascript_contexts(mako_template, contexts, results)
        for expression in expressions:
            if expression.end_index is None:
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_unparseable_expression, expression
                ))
                continue

            context = self._get_context(contexts, expression.start_index)
            self._check_filters(mako_template, expression, context, has_page_default, results)
            self._check_deprecated_display_name(expression, results)
            self._check_html_and_text(expression, has_page_default, results)

    def _check_javascript_contexts(self, mako_template, contexts, results):
        """
        Lint the JavaScript contexts for JavaScript violations inside a Mako
        template.

        Arguments:
            mako_template: The contents of the Mako template.
            contexts: A list of context dicts with 'type' and 'index'.
            results: A list of results into which violations will be added.

        Side effect:
            Adds JavaScript violations to results.
        """
        javascript_start_index = None
        for context in contexts:
            if context['type'] == 'javascript':
                if javascript_start_index < 0:
                    javascript_start_index = context['index']
            else:
                if javascript_start_index is not None:
                    javascript_end_index = context['index']
                    javascript_code = mako_template[javascript_start_index:javascript_end_index]
                    self._check_javascript_context(javascript_code, javascript_start_index, results)
                    javascript_start_index = None
        if javascript_start_index is not None:
            javascript_code = mako_template[javascript_start_index:]
            self._check_javascript_context(javascript_code, javascript_start_index, results)

    def _check_javascript_context(self, javascript_code, start_offset, results):
        """
        Lint a single JavaScript context for JavaScript violations inside a Mako
        template.

        Arguments:
            javascript_code: The template contents of the JavaScript context.
            start_offset: The offset of the JavaScript context inside the
                original Mako template.
            results: A list of results into which violations will be added.

        Side effect:
            Adds JavaScript violations to results.

        """
        javascript_results = FileResults("")
        self.javaScriptLinter.check_javascript_file_is_safe(javascript_code, javascript_results)
        # translate the violations into the location within the original
        # Mako template
        for violation in javascript_results.violations:
            expression = violation.expression
            expression.start_index += start_offset
            if expression.end_index is not None:
                expression.end_index += start_offset
            results.violations.append(ExpressionRuleViolation(violation.rule, expression))

    def _check_deprecated_display_name(self, expression, results):
        """
        Checks that the deprecated display_name_with_default_escaped is not
        used. Adds violation to results if there is a problem.

        Arguments:
            expression: An Expression
            results: A list of results into which violations will be added.

        """
        if '.display_name_with_default_escaped' in expression.expression:
            results.violations.append(ExpressionRuleViolation(
                Rules.python_deprecated_display_name, expression
            ))

    def _check_html_and_text(self, expression, has_page_default, results):
        """
        Checks rules related to proper use of HTML() and Text().

        Arguments:
            expression: A Mako Expression.
            has_page_default: True if the page is marked as default, False
                otherwise.
            results: A list of results into which violations will be added.

        """
        expression_inner = expression.expression_inner
        # use find to get the template relative inner expression start index
        # due to possible skipped white space
        template_inner_start_index = expression.start_index
        template_inner_start_index += expression.expression.find(expression_inner)
        if 'HTML(' in expression_inner:
            if expression_inner.startswith('HTML('):
                close_paren_index = self._find_closing_char_index(
                    None, "(", ")", expression_inner, start_index=len('HTML(')
                )['close_char_index']
                # check that the close paren is at the end of the stripped expression.
                if close_paren_index != len(expression_inner) - 1:
                    results.violations.append(ExpressionRuleViolation(
                        Rules.mako_html_alone, expression
                    ))
            elif expression_inner.startswith('Text(') is False:
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_html_requires_text, expression
                ))
        else:
            if 'Text(' in expression_inner:
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_text_redundant, expression
                ))

        # strings to be checked for HTML
        unwrapped_html_strings = expression.strings
        for match in re.finditer(r"(HTML\(|Text\()", expression_inner):
            result = self._find_closing_char_index(None, "(", ")", expression_inner, start_index=match.end())
            if result is not None:
                close_paren_index = result['close_char_index']
                # the argument sent to HTML() or Text()
                argument = expression_inner[match.end():close_paren_index]
                if ".format(" in argument:
                    results.violations.append(ExpressionRuleViolation(
                        Rules.python_close_before_format, expression
                    ))
                if match.group() == "HTML(":
                    # remove expression strings wrapped in HTML()
                    for string in list(unwrapped_html_strings):
                        html_inner_start_index = template_inner_start_index + match.end()
                        html_inner_end_index = template_inner_start_index + close_paren_index
                        if html_inner_start_index <= string.start_index and string.end_index <= html_inner_end_index:
                            unwrapped_html_strings.remove(string)

        # check strings not wrapped in HTML() for '<'
        for string in unwrapped_html_strings:
            if '<' in string.string_inner:
                results.violations.append(ExpressionRuleViolation(
                    Rules.python_wrap_html, expression
                ))
                break
        # check strings not wrapped in HTML() for HTML entities
        if has_page_default:
            for string in unwrapped_html_strings:
                if re.search(r"&[#]?[a-zA-Z0-9]+;", string.string_inner):
                    results.violations.append(ExpressionRuleViolation(
                        Rules.mako_html_entities, expression
                    ))
                    break

    def _check_filters(self, mako_template, expression, context, has_page_default, results):
        """
        Checks that the filters used in the given Mako expression are valid
        for the given context. Adds violation to results if there is a problem.

        Arguments:
            mako_template: The contents of the Mako template.
            expression: A Mako Expression.
            context: The context of the page in which the expression was found
                (e.g. javascript, html).
            has_page_default: True if the page is marked as default, False
                otherwise.
            results: A list of results into which violations will be added.

        """
        if context == 'unknown':
            results.violations.append(ExpressionRuleViolation(
                Rules.mako_unknown_context, expression
            ))
            return

        # Example: finds "| n, h}" when given "${x | n, h}"
        filters_regex = re.compile(r'\|([.,\w\s]*)\}')
        filters_match = filters_regex.search(expression.expression)
        if filters_match is None:
            if context == 'javascript':
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_invalid_js_filter, expression
                ))
            return

        filters = filters_match.group(1).replace(" ", "").split(",")
        if filters == ['n', 'decode.utf8']:
            # {x | n, decode.utf8} is valid in any context
            pass
        elif context == 'html':
            if filters == ['h']:
                if has_page_default:
                    # suppress this violation if the page default hasn't been set,
                    # otherwise the template might get less safe
                    results.violations.append(ExpressionRuleViolation(
                        Rules.mako_unwanted_html_filter, expression
                    ))
            else:
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_invalid_html_filter, expression
                ))
        elif context == 'javascript':
            self._check_js_expression_not_with_html(mako_template, expression, results)
            if filters == ['n', 'dump_js_escaped_json']:
                # {x | n, dump_js_escaped_json} is valid
                pass
            elif filters == ['n', 'js_escaped_string']:
                # {x | n, js_escaped_string} is valid, if surrounded by quotes
                self._check_js_string_expression_in_quotes(mako_template, expression, results)
            else:
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_invalid_js_filter, expression
                ))

    def _check_js_string_expression_in_quotes(self, mako_template, expression, results):
        """
        Checks that a Mako expression using js_escaped_string is surrounded by
        quotes.

        Arguments:
            mako_template: The contents of the Mako template.
            expression: A Mako Expression.
            results: A list of results into which violations will be added.
        """
        parse_string = self._find_string_wrapping_expression(mako_template, expression)
        if parse_string is None:
            results.violations.append(ExpressionRuleViolation(
                Rules.mako_js_missing_quotes, expression
            ))

    def _check_js_expression_not_with_html(self, mako_template, expression, results):
        """
        Checks that a Mako expression in a JavaScript context does not appear in
        a string that also contains HTML.

        Arguments:
            mako_template: The contents of the Mako template.
            expression: A Mako Expression.
            results: A list of results into which violations will be added.
        """
        parse_string = self._find_string_wrapping_expression(mako_template, expression)
        if parse_string is not None and re.search('[<>]', parse_string.string) is not None:
            results.violations.append(ExpressionRuleViolation(
                Rules.mako_js_html_string, expression
            ))

    def _find_string_wrapping_expression(self, mako_template, expression):
        """
        Finds the string wrapping the Mako expression if there is one.

        Arguments:
            mako_template: The contents of the Mako template.
            expression: A Mako Expression.

        Returns:
            ParseString representing a scrubbed version of the wrapped string,
            where the Mako expression was replaced with "${...}", if a wrapped
            string was found.  Otherwise, returns None if none found.
        """
        lines = StringLines(mako_template)
        start_index = lines.index_to_line_start_index(expression.start_index)
        if expression.end_index is not None:
            end_index = lines.index_to_line_end_index(expression.end_index)
        else:
            return None
        # scrub out the actual expression so any code inside the expression
        # doesn't interfere with rules applied to the surrounding code (i.e.
        # checking JavaScript).
        scrubbed_lines = "".join((
            mako_template[start_index:expression.start_index],
            "${...}",
            mako_template[expression.end_index:end_index]
        ))
        adjusted_start_index = expression.start_index - start_index
        start_index = 0
        while True:
            parse_string = ParseString(scrubbed_lines, start_index, len(scrubbed_lines))
            # check for validly parsed string
            if 0 <= parse_string.start_index < parse_string.end_index:
                # check if expression is contained in the given string
                if parse_string.start_index < adjusted_start_index < parse_string.end_index:
                    return parse_string
                else:
                    # move to check next string
                    start_index = parse_string.end_index
            else:
                break
        return None

    def _get_contexts(self, mako_template):
        """
        Returns a data structure that represents the indices at which the
        template changes from HTML context to JavaScript and back.

        Return:
            A list of dicts where each dict contains:
                - index: the index of the context.
                - type: the context type (e.g. 'html' or 'javascript').
        """
        contexts_re = re.compile(
            r"""
                <script.*?> |  # script tag start
                </script> |  # script tag end
                <%static:require_module.*?> |  # require js script tag start
                </%static:require_module> | # require js script tag end
                <%block[ ]*name=['"]requirejs['"]\w*> |  # require js tag start
                </%block>  # require js tag end
            """,
            re.VERBOSE | re.IGNORECASE
        )
        media_type_re = re.compile(r"""type=['"].*?['"]""", re.IGNORECASE)

        contexts = [{'index': 0, 'type': 'html'}]
        javascript_types = [
            'text/javascript', 'text/ecmascript', 'application/ecmascript', 'application/javascript',
            'text/x-mathjax-config', 'json/xblock-args'
        ]
        html_types = ['text/template']
        for context in contexts_re.finditer(mako_template):
            match_string = context.group().lower()
            if match_string.startswith("<script"):
                match_type = media_type_re.search(match_string)
                context_type = 'javascript'
                if match_type is not None:
                    # get media type (e.g. get text/javascript from
                    # type="text/javascript")
                    match_type = match_type.group()[6:-1].lower()
                    if match_type in html_types:
                        context_type = 'html'
                    elif match_type not in javascript_types:
                        context_type = 'unknown'
                contexts.append({'index': context.end(), 'type': context_type})
            elif match_string.startswith("</"):
                contexts.append({'index': context.start(), 'type': 'html'})
            else:
                contexts.append({'index': context.end(), 'type': 'javascript'})

        return contexts

    def _get_context(self, contexts, index):
        """
        Gets the context (e.g. javascript, html) of the template at the given
        index.

        Arguments:
            contexts: A list of dicts where each dict contains the 'index' of the context
                and the context 'type' (e.g. 'html' or 'javascript').
            index: The index for which we want the context.

        Returns:
             The context (e.g. javascript or html) for the given index.
        """
        current_context = contexts[0]['type']
        for context in contexts:
            if context['index'] <= index:
                current_context = context['type']
            else:
                break
        return current_context

    def _find_mako_expressions(self, mako_template):
        """
        Finds all the Mako expressions in a Mako template and creates a list
        of dicts for each expression.

        Arguments:
            mako_template: The content of the Mako template.

        Returns:
            A list of Expressions.

        """
        start_delim = '${'
        start_index = 0
        expressions = []

        while True:
            start_index = mako_template.find(start_delim, start_index)
            if start_index < 0:
                break

            result = self._find_closing_char_index(
                start_delim, '{', '}', mako_template, start_index=start_index + len(start_delim)
            )
            if result is None:
                expression = Expression(start_index)
                # for parsing error, restart search right after the start of the
                # current expression
                start_index = start_index + len(start_delim)
            else:
                close_char_index = result['close_char_index']
                expression = mako_template[start_index:close_char_index + 1]
                expression = Expression(
                    start_index,
                    end_index=close_char_index + 1,
                    template=mako_template,
                    start_delim=start_delim,
                    end_delim='}',
                    strings=result['strings'],
                )
                # restart search after the current expression
                start_index = expression.end_index
            expressions.append(expression)
        return expressions


def _process_file(full_path, template_linters, options, out):
    """
    For each linter, lints the provided file.  This means finding and printing
    violations.

    Arguments:
        full_path: The full path of the file to lint.
        template_linters: A list of linting objects.
        options: A list of the options.
        out: output file

    Returns:
        The number of violations.

    """
    num_violations = 0
    directory = os.path.dirname(full_path)
    file_name = os.path.basename(full_path)
    for template_linter in template_linters:
        results = template_linter.process_file(directory, file_name)
        num_violations += results.print_results(options, out)
    return num_violations


def _process_current_walk(current_walk, template_linters, options, out):
    """
    For each linter, lints all the files in the current os walk.  This means
    finding and printing violations.

    Arguments:
        current_walk: A walk returned by os.walk().
        template_linters: A list of linting objects.
        options: A list of the options.
        out: output file

    Returns:
        The number of violations.

    """
    num_violations = 0
    walk_directory = os.path.normpath(current_walk[0])
    walk_files = current_walk[2]
    for walk_file in walk_files:
        full_path = os.path.join(walk_directory, walk_file)
        num_violations += _process_file(full_path, template_linters, options, out)
    return num_violations


def _process_os_walk(starting_dir, template_linters, options, out):
    """
    For each linter, lints all the directories in the starting directory.

    Arguments:
        starting_dir: The initial directory to begin the walk.
        template_linters: A list of linting objects.
        options: A list of the options.
        out: output file

    Returns:
        The number of violations.

    """
    num_violations = 0
    for current_walk in os.walk(starting_dir):
        num_violations += _process_current_walk(current_walk, template_linters, options, out)
    return num_violations


def main():
    """
    Used to execute the linter. Use --help option for help.

    Prints all violations.
    """
    epilog = 'rules:\n'
    for rule in Rules.__members__.values():
        epilog += "  {0[0]}: {0[1]}\n".format(rule.value)
    epilog += "\n"
    epilog += "additional help:\n"
    # pylint: disable=line-too-long
    epilog += "  http://edx.readthedocs.org/projects/edx-developer-guide/en/latest/conventions/safe_templates.html#safe-template-linter\n"

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Checks that templates are safe.',
        epilog=epilog,
    )
    parser.add_argument(
        '--list-files', dest='list_files', action='store_true',
        help='Only display the filenames that contain violations.'
    )
    parser.add_argument('path', nargs="?", default=None, help='A file to lint or directory to recursively lint.')

    args = parser.parse_args()

    options = {
        'list_files': args.list_files,
    }
    template_linters = [MakoTemplateLinter(), UnderscoreTemplateLinter(), JavaScriptLinter(), PythonLinter()]

    if args.path is not None and os.path.isfile(args.path):
        num_violations = _process_file(args.path, template_linters, options, out=sys.stdout)
    else:
        directory = "."
        if args.path is not None:
            if os.path.exists(args.path):
                directory = args.path
            else:
                raise ValueError("Path [{}] is not a valid file or directory.".format(args.path))
        num_violations = _process_os_walk(directory, template_linters, options, out=sys.stdout)

    if options['list_files'] is False:
        # matches output of jshint for simplicity
        print("")
        print("{} violations found".format(num_violations))


if __name__ == "__main__":
    main()
