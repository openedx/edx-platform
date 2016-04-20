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

_skip_dirs = (
    '.pycharm_helpers',
    'common/static/xmodule/modules',
    'node_modules',
    'reports/diff_quality',
    'spec',
    'scripts/tests/templates',
    'test_root',
    'vendor',
)


def _is_skip_dir(skip_dirs, directory):
    """
    Determines whether a directory should be skipped or linted.

    Arguments:
        skip_dirs: The configured directories to be skipped.
        directory: The current directory to be tested.

    Returns:
         True if the directory should be skipped, and False otherwise.

    """
    for skip_dir in skip_dirs:
        dir_contains_skip_dir = '/' + skip_dir + '/' in directory
        if dir_contains_skip_dir or directory.startswith(skip_dir) or directory.endswith(skip_dir):
            return True
    return False


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
        self._line_breaks = self._process_line_breaks(string)

    def _process_line_breaks(self, string):
        """
        Creates a list, where each entry represents the index into the string
        where the next line break was found.

        Arguments:
            string: The string in which to find line breaks.

        Returns:
             A list of indices into the string at which each line break can be
             found.

        """
        line_breaks = [0]
        index = 0
        while True:
            index = string.find('\n', index)
            if index < 0:
                break
            index += 1
            line_breaks.append(index)
        return line_breaks

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
        for line_break_index in self._line_breaks:
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

    def line_number_to_start_index(self, line_number):
        """
        Gets the starting index for the provided line number.

        Arguments:
            line_number: The line number of the line for which we want to find
                the start index.

        Returns:
            The starting index for the provided line number.

        """
        return self._line_breaks[line_number - 1]

    def line_number_to_line(self, line_number):
        """
        Gets the line of text designated by the provided line number.

        Arguments:
            line_number: The line number of the line we want to find.

        Returns:
            The line of text designated by the provided line number.

        """
        start_index = self._line_breaks[line_number - 1]
        if len(self._line_breaks) == line_number:
            line = self._string[start_index:]
        else:
            end_index = self._line_breaks[line_number]
            line = self._string[start_index:end_index - 1]
        return line

    def line_count(self):
        """
        Gets the number of lines in the string.
        """
        return len(self._line_breaks)


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
    mako_deprecated_display_name = (
        'mako-deprecated-display-name',
        'Replace deprecated display_name_with_default_escaped with display_name_with_default.'
    )
    mako_html_requires_text = (
        'mako-html-requires-text',
        'You must begin with Text() if you use HTML() during interpolation.'
    )
    mako_close_before_format = (
        'mako-close-before-format',
        'You must close any call to Text() or HTML() before calling format().'
    )
    mako_text_redundant = (
        'mako-text-redundant',
        'Using Text() function without HTML() is unnecessary.'
    )
    mako_html_alone = (
        'mako-html-alone',
        "Only use HTML() alone with properly escaped HTML(), and make sure it is really alone."
    )
    mako_wrap_html = (
        'mako-wrap-html',
        "String containing HTML should be wrapped with call to HTML()."
    )
    underscore_not_escaped = (
        'underscore-not-escaped',
        'Expressions should be escaped using <%- expression %>.'
    )

    def __init__(self, rule_id, rule_summary):
        self.rule_id = rule_id
        self.rule_summary = rule_summary


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
            expression: The expression that was in violation.

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

    def prepare_results(self, full_path, string_lines):
        """
        Preps this instance for results reporting.

        Arguments:
            full_path: Path of the file in violation.
            string_lines: A StringLines containing the contents of the file in
                violation.

        """
        self.full_path = full_path
        start_index = self.expression['start_index']
        self.start_line = string_lines.index_to_line_number(start_index)
        self.start_column = string_lines.index_to_column_number(start_index)
        end_index = self.expression['end_index']
        if end_index > 0:
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

    def prepare_results(self, file_string):
        """
        Prepares the results for output for this file.

        Arguments:
            file_string: The string of content for this file.

        """
        string_lines = StringLines(file_string)
        for violation in self.violations:
            violation.prepare_results(self.full_path, string_lines)

    def print_results(self, options, out):
        """
        Prints the results (i.e. violations) in this file.

        Arguments:
            options: A list of the following options:
                is_quiet: True to print only file names, and False to print
                    all violations.
            out: output file


        """
        if options['is_quiet']:
            print(self.full_path, file=out)
        else:
            for violation in self.violations:
                if not violation.is_disabled:
                    violation.print_results(out)


class ParseString(object):
    """
    ParseString is the result of parsing a string out of a template.

    A ParseString has the following attributes:
        start_index: The index of the first quote, or -1 if none found
        end_index: The index following the closing quote, or -1 if
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
        self.end_index = -1
        self.quote_length = None
        self.string = None
        self.string_inner = None
        self.start_index = self._find_string_start(template, start_index, end_index)
        if 0 <= self.start_index:
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
            The start index of the first single or double quote, or -1 if
            no quote was found.
        """
        quote_regex = re.compile(r"""['"]""")
        start_match = quote_regex.search(template, start_index, end_index)
        if start_match is None:
            return -1
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


class MakoTemplateLinter(object):
    """
    The linter for Mako template files.
    """

    _skip_mako_dirs = _skip_dirs

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

        return self._load_and_check_mako_file_is_safe(mako_file_full_path, results)

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
        if _is_skip_dir(self._skip_mako_dirs, directory):
            return False

        # TODO: This is an imperfect guess concerning the Mako template
        # directories. This needs to be reviewed before turning on safe by
        # default at the platform level.
        if ('/templates/' in directory) or directory.endswith('/templates'):
            return True

        return False

    def _load_and_check_mako_file_is_safe(self, mako_file_full_path, results):
        """
        Loads the Mako template file and checks if it is in violation.

        Arguments:
            mako_file_full_path: The file to be loaded and linted.

        Returns:
            The file results containing any violations.

        """
        mako_template = _load_file(self, mako_file_full_path)
        self._check_mako_file_is_safe(mako_template, results)
        return results

    def _check_mako_file_is_safe(self, mako_template, results):
        """
        Checks for violations in a Mako template.

        Arguments:
            mako_template: The contents of the Mako template.
            results: A file results objects to which violations will be added.

        """
        if self._is_django_template(mako_template):
            return
        has_page_default = False
        if self._has_multiple_page_tags(mako_template):
            results.violations.append(RuleViolation(Rules.mako_multiple_page_tags))
        else:
            has_page_default = self._has_page_default(mako_template)
            if not has_page_default:
                results.violations.append(RuleViolation(Rules.mako_missing_default))
        self._check_mako_expressions(mako_template, has_page_default, results)
        results.prepare_results(mako_template)

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

    def _has_multiple_page_tags(self, mako_template):
        """
        Checks if the Mako template contains more than one page expression.

        Arguments:
            mako_template: The contents of the Mako template.

        """
        count = len(re.findall('<%page ', mako_template, re.IGNORECASE))
        return count > 1

    def _has_page_default(self, mako_template):
        """
        Checks if the Mako template contains the page expression marking it as
        safe by default.

        Arguments:
            mako_template: The contents of the Mako template.

        """
        page_h_filter_regex = re.compile('<%page[^>]*expression_filter=(?:"h"|\'h\')[^>]*/>')
        page_match = page_h_filter_regex.search(mako_template)
        return page_match

    def _check_mako_expressions(self, mako_template, has_page_default, results):
        """
        Searches for Mako expressions and then checks if they contain
        violations.

        Arguments:
            mako_template: The contents of the Mako template.
            has_page_default: True if the page is marked as default, False
                otherwise.
            results: A list of results into which violations will be added.

        """
        expressions = self._find_mako_expressions(mako_template)
        contexts = self._get_contexts(mako_template)
        for expression in expressions:
            if expression['expression'] is None:
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_unparseable_expression, expression
                ))
                continue

            context = self._get_context(contexts, expression['start_index'])
            self._check_filters(mako_template, expression, context, has_page_default, results)
            self._check_deprecated_display_name(expression, results)
            self._check_html_and_text(expression, results)

    def _check_deprecated_display_name(self, expression, results):
        """
        Checks that the deprecated display_name_with_default_escaped is not
        used. Adds violation to results if there is a problem.

        Arguments:
            expression: A dict containing the start_index, end_index, and
                expression (text) of the expression.
            results: A list of results into which violations will be added.

        """
        if '.display_name_with_default_escaped' in expression['expression']:
            results.violations.append(ExpressionRuleViolation(
                Rules.mako_deprecated_display_name, expression
            ))

    def _check_html_and_text(self, expression, results):
        """
        Checks rules related to proper use of HTML() and Text().

        Arguments:
            expression: A dict containing the start_index, end_index, and
                expression (text) of the expression.
            results: A list of results into which violations will be added.

        """
        # strip '${' and '}' and whitespace from ends
        expression_inner = expression['expression'][2:-1].strip()
        # find the template relative inner expression start index
        # - find used to take into account above strip()
        template_inner_start_index = expression['start_index'] + expression['expression'].find(expression_inner)
        if 'HTML(' in expression_inner:
            if expression_inner.startswith('HTML('):
                close_paren_index = self._find_closing_char_index(
                    None, "(", ")", expression_inner, start_index=len('HTML('), num_open_chars=0, strings=[]
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
        unwrapped_html_strings = expression['strings']
        for match in re.finditer(r"(HTML\(|Text\()", expression_inner):
            result = self._find_closing_char_index(
                None, "(", ")", expression_inner, start_index=match.end(), num_open_chars=0, strings=[]
            )
            close_paren_index = result['close_char_index']
            if 0 <= close_paren_index:
                # the argument sent to HTML() or Text()
                argument = expression_inner[match.end():close_paren_index]
                if ".format(" in argument:
                    results.violations.append(ExpressionRuleViolation(
                        Rules.mako_close_before_format, expression
                    ))
                if match.group() == "HTML(":
                    # remove expression strings wrapped in HTML()
                    for string in list(unwrapped_html_strings):
                        html_inner_start_index = template_inner_start_index + match.end()
                        html_inner_end_index = template_inner_start_index + close_paren_index
                        if html_inner_start_index <= string.start_index and string.end_index <= html_inner_end_index:
                            unwrapped_html_strings.remove(string)

        # check strings not wrapped in HTML()
        for string in unwrapped_html_strings:
            if '<' in string.string_inner:
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_wrap_html, expression
                ))
                break

    def _check_filters(self, mako_template, expression, context, has_page_default, results):
        """
        Checks that the filters used in the given Mako expression are valid
        for the given context. Adds violation to results if there is a problem.

        Arguments:
            mako_template: The contents of the Mako template.
            expression: A dict containing the start_index, end_index, and
                expression (text) of the expression.
            context: The context of the page in which the expression was found
                (e.g. javascript, html).
            has_page_default: True if the page is marked as default, False
                otherwise.
            results: A list of results into which violations will be added.

        """
        # finds "| n, h}" when given "${x | n, h}"
        filters_regex = re.compile('\|[a-zA-Z_,\s]*\}')
        filters_match = filters_regex.search(expression['expression'])
        if filters_match is None:
            if context == 'javascript':
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_invalid_js_filter, expression
                ))
            return

        filters = filters_match.group()[1:-1].replace(" ", "").split(",")
        if (len(filters) == 2) and (filters[0] == 'n') and (filters[1] == 'unicode'):
            # {x | n, unicode} is valid in any context
            pass
        elif context == 'html':
            if (len(filters) == 1) and (filters[0] == 'h'):
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

        else:
            if (len(filters) == 2) and (filters[0] == 'n') and (filters[1] == 'dump_js_escaped_json'):
                # {x | n, dump_js_escaped_json} is valid
                pass
            elif (len(filters) == 2) and (filters[0] == 'n') and (filters[1] == 'js_escaped_string'):
                # {x | n, js_escaped_string} is valid, if surrounded by quotes
                pass
            else:
                results.violations.append(ExpressionRuleViolation(
                    Rules.mako_invalid_js_filter, expression
                ))

    def _get_contexts(self, mako_template):
        """
        Returns a data structure that represents the indices at which the
        template changes from HTML context to JavaScript and back.

        Return:
            A list of dicts where each dict contains the 'index' of the context
            and the context 'type' (e.g. 'html' or 'javascript').
        """
        contexts_re = re.compile(r"""
            <script.*?>|  # script tag start
            </script>|  # script tag end
            <%static:require_module.*?>|  # require js script tag start
            </%static:require_module>  # require js script tag end""", re.VERBOSE | re.IGNORECASE)
        media_type_re = re.compile(r"""type=['"].*?['"]""", re.IGNORECASE)

        contexts = [{'index': 0, 'type': 'html'}]
        for context in contexts_re.finditer(mako_template):
            match_string = context.group().lower()
            if match_string.startswith("<script"):
                match_type = media_type_re.search(match_string)
                context_type = 'javascript'
                if match_type is not None:
                    # get media type (e.g. get text/javascript from
                    # type="text/javascript")
                    match_type = match_type.group()[6:-1].lower()
                    if match_type not in [
                        'text/javascript',
                        'text/ecmascript',
                        'application/ecmascript',
                        'application/javascript',
                    ]:
                        #TODO: What are other types found, and are these really
                        # html?  Or do we need to properly handle unknown
                        # contexts?
                        context_type = 'html'
                contexts.append({'index': context.end(), 'type': context_type})
            elif match_string.startswith("</script"):
                contexts.append({'index': context.start(), 'type': 'html'})
            elif match_string.startswith("<%static:require_module"):
                contexts.append({'index': context.end(), 'type': 'javascript'})
            else:
                contexts.append({'index': context.start(), 'type': 'html'})

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
            A list of dicts for each expression, where the dict contains the
            following:

                start_index: The index of the start of the expression.
                end_index: The index immediately following the expression, or -1
                    if unparseable.
                expression: The text of the expression.
                strings: a list of ParseStrings

        """
        start_delim = '${'
        start_index = 0
        expressions = []

        while True:
            start_index = mako_template.find(start_delim, start_index)
            if start_index < 0:
                break

            result = self._find_closing_char_index(
                start_delim, '{', '}', mako_template, start_index=start_index + len(start_delim),
                num_open_chars=0, strings=[]
            )
            close_char_index = result['close_char_index']
            if close_char_index < 0:
                expression = None
            else:
                expression = mako_template[start_index:close_char_index + 1]

            expression = {
                'start_index': start_index,
                'end_index': close_char_index + 1,
                'expression': expression,
                'strings': result['strings'],
            }
            expressions.append(expression)

            # end_index of -1 represents a parsing error and we may find others
            start_index = max(start_index + len(start_delim), close_char_index)

        return expressions

    def _find_closing_char_index(
            self, start_delim, open_char, close_char, template, start_index, num_open_chars, strings
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
            A dict containing the following:
                close_char_index: The index of the closing character, or -1 if
                unparseable.
                strings: a list of ParseStrings

        """
        unparseable_result = {'close_char_index': -1, 'strings': []}
        close_char_index = template.find(close_char, start_index)
        if close_char_index < 0:
            # if we can't find an end_char, let's just quit
            return unparseable_result
        open_char_index = template.find(open_char, start_index, close_char_index)
        parse_string = ParseString(template, start_index, close_char_index)

        valid_index_list = [close_char_index]
        if 0 <= open_char_index:
            valid_index_list.append(open_char_index)
        if 0 <= parse_string.start_index:
            valid_index_list.append(parse_string.start_index)
        min_valid_index = min(valid_index_list)

        if parse_string.start_index == min_valid_index:
            strings.append(parse_string)
            if parse_string.end_index < 0:
                return unparseable_result
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
                    return unparseable_result
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


class UnderscoreTemplateLinter(object):
    """
    The linter for Underscore.js template files.
    """

    _skip_underscore_dirs = _skip_dirs + ('test',)

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

        if not self._is_valid_directory(directory):
            return results

        if not file_name.lower().endswith('.underscore'):
            return results

        return self._load_and_check_underscore_file_is_safe(full_path, results)

    def _is_valid_directory(self, directory):
        """
        Determines if the provided directory is a directory that could contain
        Underscore.js template files that need to be linted.

        Arguments:
            directory: The directory to be linted.

        Returns:
            True if this directory should be linted for Underscore.js template
            violations and False otherwise.
        """
        if _is_skip_dir(self._skip_underscore_dirs, directory):
            return False

        return True

    def _load_and_check_underscore_file_is_safe(self, file_full_path, results):
        """
        Loads the Underscore.js template file and checks if it is in violation.

        Arguments:
            file_full_path: The file to be loaded and linted

        Returns:
            The file results containing any violations.

        """
        underscore_template = _load_file(self, file_full_path)
        self._check_underscore_file_is_safe(underscore_template, results)
        return results

    def _check_underscore_file_is_safe(self, underscore_template, results):
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
            expression: The expression being checked.

        Returns:
            True if the expression has been safely escaped, and False otherwise.

        """
        if expression['expression_inner'].startswith('HtmlUtils.'):
            return True
        if expression['expression_inner'].startswith('_.escape('):
            return True
        return False

    def _find_unescaped_expressions(self, underscore_template):
        """
        Returns a list of unsafe expressions.

        At this time all expressions that are unescaped are considered unsafe.

        Arguments:
            underscore_template: The contents of the Underscore.js template.

        Returns:
            A list of dicts for each expression, where the dict contains the
            following:

                start_index: The index of the start of the expression.
                end_index: The index of the end of the expression.
                expression: The text of the expression.
        """
        unescaped_expression_regex = re.compile("<%=(.*?)%>", re.DOTALL)

        expressions = []
        for match in unescaped_expression_regex.finditer(underscore_template):
            expression = {
                'start_index': match.start(),
                'end_index': match.end(),
                'expression': match.group(),
                'expression_inner': match.group(1).strip()
            }
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

    """
    directory = os.path.dirname(full_path)
    file = os.path.basename(full_path)
    for template_linter in template_linters:
        results = template_linter.process_file(directory, file)
        results.print_results(options, out)


def _process_current_walk(current_walk, template_linters, options, out):
    """
    For each linter, lints all the files in the current os walk.  This means
    finding and printing violations.

    Arguments:
        current_walk: A walk returned by os.walk().
        template_linters: A list of linting objects.
        options: A list of the options.
        out: output file

    """
    walk_directory = os.path.normpath(current_walk[0])
    walk_files = current_walk[2]
    for walk_file in walk_files:
        full_path = os.path.join(walk_directory, walk_file)
        _process_file(full_path, template_linters, options, out)


def _process_os_walk(starting_dir, template_linters, options, out):
    """
    For each linter, lints all the directories in the starting directory.

    Arguments:
        starting_dir: The initial directory to begin the walk.
        template_linters: A list of linting objects.
        options: A list of the options.
        out: output file

    """
    for current_walk in os.walk(starting_dir):
        _process_current_walk(current_walk, template_linters, options, out)


def _parse_arg(arg, option):
    """
    Parses an argument searching for --[option]=[OPTION_VALUE]

    Arguments:
        arg: The system argument
        option: The specific option to be searched for (e.g. "file")

    Returns:
        The option value for a match, or None if arg is not for this option
    """
    if arg.startswith('--{}='.format(option)):
        option_value = arg.split('=')[1]
        if option_value.startswith("'") or option_value.startswith('"'):
            option_value = option_value[1:-1]
        return option_value
    else:
        return None


def main():
    """
    Used to execute the linter. Use --help option for help.

    Prints all violations.
    """
    epilog = 'rules:\n'
    for rule in Rules.__members__.values():
        epilog += "  {0[0]}: {0[1]}\n".format(rule.value)

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Checks that templates are safe.',
        epilog=epilog
    )
    parser.add_argument('--quiet', dest='quiet', action='store_true', help='only display the filenames that contain violations')
    parser.add_argument('--file', dest='file', nargs=1, default=None, help='a single file to lint')
    parser.add_argument('--dir', dest='directory', nargs=1, default=['.'], help='the directory to lint (including sub-directories)')

    args = parser.parse_args()

    options = {
        'is_quiet': args.quiet,
    }

    template_linters = [MakoTemplateLinter(), UnderscoreTemplateLinter()]
    if args.file is not None:
        if os.path.isfile(args.file[0]) is False:
            raise ValueError("File [{}] is not a valid file.".format(args.file[0]))
        _process_file(args.file[0], template_linters, options, out=sys.stdout)
    else:
        if os.path.exists(args.directory[0]) is False or os.path.isfile(args.directory[0]) is True:
            raise ValueError("Directory [{}] is not a valid directory.".format(args.directory[0]))
        _process_os_walk(args.directory[0], template_linters, options, out=sys.stdout)


if __name__ == "__main__":
    main()
