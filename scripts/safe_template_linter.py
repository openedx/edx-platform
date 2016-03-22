#!/usr/bin/env python
"""
A linting tool to check if templates are safe
"""
from enum import Enum
import os
import re
import sys

_skip_dirs = (
    '/node_modules',
    '/vendor',
    '/spec',
    '/.pycharm_helpers',
    '/test_root',
    '/reports/diff_quality',
    '/common/static/xmodule/modules',
)
_skip_mako_dirs = _skip_dirs
_skip_underscore_dirs = _skip_dirs + ('/test',)


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
        dir_contains_skip_dir = (directory.find(skip_dir + '/') >= 0)
        if dir_contains_skip_dir or directory.endswith(skip_dir):
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


def _get_line_breaks(self, string):
    """
    Creates a list, where each entry represents the index into the string where
    the next line break was found.

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


def _get_line_number(self, line_breaks, index):
    """
    Given the list of line break indices, and an index, determines the line of
    the index.

    Arguments:
        line_breaks: A list of indices into a string at which each line break
            was found.
        index: The index into the original string for which we want to know the
            line number

    Returns:
        The line number of the provided index.

    """
    current_line_number = 0
    for line_break_index in line_breaks:
        if line_break_index <= index:
            current_line_number += 1
        else:
            break
    return current_line_number


def _get_line(self, string, line_breaks, line_number):
    """
    Gets the line of text designated by the provided line number.

    Arguments:
        string: The string of content with line breaks.
        line_breaks: A list of indices into a string at which each line break
            was found.
        line_number: The line number of the line we want to find.

    Returns:
        The line of text designated by the provided line number.

    """
    start_index = line_breaks[line_number - 1]
    if len(line_breaks) == line_number:
        line = string[start_index:]
    else:
        end_index = line_breaks[line_number]
        line = string[start_index:end_index - 1]
    return line.encode(encoding='utf-8')


def _get_column_number(self, line_breaks, line_number, index):
    """
    Gets the column (i.e. index into the line) for the given index into the
    original string.

    Arguments:
        line_breaks: A list of indices into a string at which each line break
            was found.
        line_number: The line number of the line we want to find.
        index: The index into the original string.

    Returns:
        The column (i.e. index into the line) for the given index into the
        original string.

    """
    start_index = line_breaks[line_number - 1]
    column = index - start_index + 1
    return column


class Rules(Enum):
    """
    An Enum of each rule which the linter will check.
    """
    mako_missing_default = ('mako-missing-default', 'The default page directive with h filter is missing.')
    mako_unparsable_expression = ('mako-unparsable-expression', 'The expression could not be properly parsed.')
    mako_unwanted_html_filter = ('mako-unwanted-html-filter', 'Remove explicit h filters when it is provided by the page directive.')
    mako_invalid_html_filter = ('mako-invalid-html-filter', 'The expression is using an invalid filter in an HTML context.')
    mako_invalid_js_filter = ('mako-invalid-js-filter', 'The expression is using an invalid filter in a JavaScript context.')
    mako_js_string_missing_quotes = ('mako-js-string-missing-quotes', 'An expression using the js_escape_string filter must have surrounding quotes.')

    underscore_not_escaped = ('underscore-not-escaped', 'Expressions should be escaped using <%- expression %>.')

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

    def prepare_results(self, full_path, file_string, line_breaks):
        """
        Preps this instance for results reporting.

        Arguments:
            full_path: Path of the file in violation.
            file_string: The contents of the file in violation.
            line_breaks: A list of indices into file_string at which each line
                break was found.

        """
        self.full_path = full_path

    def print_results(self):
        """
        Prints the results represented by this rule violation.
        """
        print "{}: {}".format(self.full_path, self.rule.rule_id)


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

    def prepare_results(self, full_path, file_string, line_breaks):
        """
        Preps this instance for results reporting.

        Arguments:
            full_path: Path of the file in violation.
            file_string: The contents of the file in violation.
            line_breaks: A list of indices into file_string at which each line
                break was found.

        """
        self.full_path = full_path
        start_index = self.expression['start_index']
        self.start_line = _get_line_number(self, line_breaks, start_index)
        self.start_column = _get_column_number(self, line_breaks, self.start_line, start_index)
        end_index = self.expression['end_index']
        if end_index > 0:
            self.end_line = _get_line_number(self, line_breaks, end_index)
            self.end_column = _get_column_number(self, line_breaks, self.end_line, end_index)
        else:
            self.end_line = self.start_line
            self.end_column = '?'
        for line_number in range(self.start_line, self.end_line + 1):
            self.lines.append(_get_line(self, file_string, line_breaks, line_number))

    def print_results(self):
        """
        Prints the results represented by this rule violation.
        """
        for line_number in range(self.start_line, self.end_line + 1):
            if (line_number == self.start_line):
                column = self.start_column
                rule_id = self.rule.rule_id + ":"
            else:
                column = 1
                rule_id = " " * (len(self.rule.rule_id) + 1)
            print "{}: {}:{}: {} {}".format(
                self.full_path,
                line_number,
                column,
                rule_id,
                self.lines[line_number - self.start_line - 1]
            )


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
        self.violations = []

    def prepare_results(self, file_string):
        """
        Prepares the results for output for this file.

        Arguments:
            file_string: The string of content for this file.

        """
        line_breaks = _get_line_breaks(self, file_string)
        for violation in self.violations:
            violation.prepare_results(self.full_path, file_string, line_breaks)

    def print_results(self, options):
        """
        Prints the results (i.e. violations) in this file.

        Arguments:
            options: A list of the following options:
                is_quiet: True to print only file names, and False to print
                    all violations.

        """
        if options['is_quiet']:
            print self.full_path
        else:
            for violation in self.violations:
                violation.print_results()


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
            The file results containing any violations, or None if the file is
            never checked.

        """
        if not self._is_mako_directory(directory):
            return None

        # TODO: When safe-by-default is turned on at the platform level, will we:
        # 1. Turn it on for .html only, or
        # 2. Turn it on for all files, and have different rulesets that have
        #    different rules of .xml, .html, .js, .txt Mako templates (e.g. use
        #    the n filter to turn off h for some of these)?
        # For now, we only check .html and .xml files
        if not (file_name.lower().endswith('.html') or file_name.lower().endswith('.xml')):
            return None

        return self._load_and_check_mako_file_is_safe(directory + '/' + file_name)

    def _is_mako_directory(self, directory):
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

        if (directory.find('/templates/') >= 0) or directory.endswith('/templates'):
            return True

        return False

    def _load_and_check_mako_file_is_safe(self, mako_file_full_path):
        """
        Loads the Mako template file and checks if it is in violation.

        Arguments:
            mako_file_full_path: The file to be loaded and linted.

        Returns:
            The file results containing any violations, or None if none found.

        """
        mako_template = _load_file(self, mako_file_full_path)
        results = FileResults(mako_file_full_path)
        self._check_mako_file_is_safe(mako_template, results)
        if len(results.violations) > 0:
            return results
        else:
            return None

    def _check_mako_file_is_safe(self, mako_template, results):
        """
        Checks for violations in a Mako template.

        Arguments:
            mako_template: The contents of the Mako template.
            results: A file results objects to which violations will be added.

        """
        has_page_default = self._has_page_default(mako_template, results)
        if not has_page_default:
            results.violations.append(RuleViolation(Rules.mako_missing_default))
        self._check_mako_expressions(mako_template, has_page_default, results)
        results.prepare_results(mako_template)

    def _has_page_default(self, mako_template, results):
        """
        Checks if the Mako template contains the page expression marking it as
        safe by default.

        Arguments:
            mako_template: The contents of the Mako template.
            results: A list of results into which violations will be added.

        """
        page_h_filter_regex = re.compile('<%page expression_filter=(?:"h"|\'h\')\s*/>')
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
                    Rules.mako_unparsable_expression, expression
                ))
                continue

            context = self._get_context(contexts, expression['start_index'])
            self._check_filters(mako_template, expression, context, has_page_default, results)

    def _check_filters(self, mako_template, expression, context, has_page_default, results):
        """
        Checks that the filters used in the given Mako expression are valid
        for the given context.

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
        if context == 'html':
            if (len(filters) == 1) and (filters[0] == 'h'):
                if has_page_default:
                    # suppress this violation if the page default hasn't been set,
                    # otherwise the template might get less safe
                    results.violations.append(ExpressionRuleViolation(
                        Rules.mako_unwanted_html_filter, expression
                    ))
            elif (len(filters) == 2) and (filters[0] == 'n') and (filters[1] == 'dump_html_escaped_json'):
                # {x | n, dump_html_escaped_json} is valid
                pass
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
                prior_character = mako_template[expression['start_index'] - 1]
                next_character = mako_template[expression['end_index'] + 1]
                has_surrounding_quotes = (prior_character == '\'' and next_character == '\'') or \
                    (prior_character == '"' and next_character == '"')
                if not has_surrounding_quotes:
                    results.violations.append(ExpressionRuleViolation(
                        Rules.mako_js_string_missing_quotes, expression
                    ))
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
            </%static:require_module>  # require js script tag end""", re.VERBOSE + re.IGNORECASE)
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
                end_index: The index of the end of the expression, or -1 if
                    unparseable.
                expression: The text of the expression.
        """
        start_delim = '${'
        start_index = 0
        expressions = []

        while True:
            start_index = mako_template.find(start_delim, start_index)
            if (start_index < 0):
                break
            end_index = self._find_balanced_end_curly(mako_template, start_index + len(start_delim), 0)

            if end_index < 0:
                expression = None
            else:
                expression = mako_template[start_index:end_index + 1]

            expression = {
                'start_index': start_index,
                'end_index': end_index,
                'expression': expression
            }
            expressions.append(expression)

            # end_index of -1 represents a parsing error and we may find others
            start_index = max(start_index + len(start_delim), end_index)

        return expressions

    def _find_balanced_end_curly(self, mako_template, start_index, num_open_curlies):
        """
        Finds the end index of the Mako expression's ending curly brace.  Skips
        any additional open/closed braces that are balanced inside.  Does not
        take into consideration strings.

        Arguments:
            mako_template: The template text.
            start_index: The start index of the Mako expression.
            num_open_curlies: The current number of open expressions.

        Returns:
            The end index of the expression, or -1 if unparseable.
        """
        end_curly_index = mako_template.find('}', start_index)
        if end_curly_index < 0:
            # if we can't find an end_curly, let's just quit
            return end_curly_index

        open_curly_index = mako_template.find('{', start_index, end_curly_index)

        if (open_curly_index >= 0) and (open_curly_index < end_curly_index):
            if mako_template[open_curly_index - 1] == '$':
                # assume if we find "${" it is the start of the next expression
                # and we have a parse error
                return -1
            else:
                return self._find_balanced_end_curly(mako_template, open_curly_index + 1, num_open_curlies + 1)

        if num_open_curlies == 0:
            return end_curly_index
        else:
            return self._find_balanced_end_curly(mako_template, end_curly_index + 1, num_open_curlies - 1)


class UnderscoreTemplateLinter(object):
    """
    The linter for Underscore.js template files.
    """

    _skip_underscore_dirs = _skip_dirs

    def process_file(self, directory, file_name):
        """
        Process file to determine if it is an Underscore template file and
        if it is safe.

        Arguments:
            directory (string): The directory of the file to be checked
            file_name (string): A filename for a potential underscore file

        Returns:
            The file results containing any violations, or None if the file is
            never checked.

        """
        if not self._is_underscore_directory(directory):
            return

        if not file_name.lower().endswith('.underscore'):
            return

        full_path = directory + '/' + file_name
        return self._load_and_check_underscore_file_is_safe(full_path)

    def print_results(self, options):
        """
        Prints all results (i.e. violations) for all files that failed this
        linter.

        Arguments:
            options: A list of the options.

        """
        for result in self._results:
            result.print_results(options)

    def _is_underscore_directory(self, directory):
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

    def _load_and_check_underscore_file_is_safe(self, file_full_path):
        """
        Loads the Underscore.js template file and checks if it is in violation.

        Arguments:
            file_full_path: The file to be loaded and linted

        Returns:
            The file results containing any violations, or None if the file is
            never checked.

        """
        underscore_template = _load_file(self, file_full_path)
        results = FileResults(file_full_path)
        self._check_underscore_file_is_safe(underscore_template, results)
        if len(results.violations) > 0:
            return results
        else:
            return None

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
            results.violations.append(ExpressionRuleViolation(
                Rules.underscore_not_escaped, expression
            ))

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
        unescaped_expression_regex = re.compile("<%=.*?%>")

        expressions = []
        for match in unescaped_expression_regex.finditer(underscore_template):
            expression = {
                'start_index': match.start(),
                'end_index': match.end(),
                'expression': match.group(),
            }
            expressions.append(expression)

        return expressions


def _process_current_walk(current_walk, template_linters, options):
    """
    For each linter, lints all the files in the current os walk.  This means
    finding and printing violations.

    Arguments:
        current_walk: A walk returned by os.walk().
        template_linters: A list of linting objects.
        options: A list of the options.

    """
    walk_directory = current_walk[0]
    walk_files = current_walk[2]
    for walk_file in walk_files:
        for template_linter in template_linters:
            results = template_linter.process_file(walk_directory, walk_file)
            if results is not None:
                results.print_results(options)


def _process_os_walk(starting_dir, template_linters, options):
    """
    For each linter, lints all the directories in the starting directory.

    Arguments:
        starting_dir: The initial directory to begin the walk.
        template_linters: A list of linting objects.
        options: A list of the options.

    """
    for current_walk in os.walk(starting_dir):
        _process_current_walk(current_walk, template_linters, options)


def main():
    """
    Used to execute the linter. Use --help option for help.

    Prints all of the violations.
    """
    #TODO: Use click
    if '--help' in sys.argv:
        print "Check that templates are safe."
        print "Options:"
        print "   --quiet    Just display the filenames with violations."
        print
        print "Rules:"
        for rule in Rules.__members__.values():
            print "  {0[0]}: {0[1]}".format(rule.value)
        return

    is_quiet = '--quiet' in sys.argv

    options = {
        'is_quiet': is_quiet,
    }

    template_linters = [MakoTemplateLinter(), UnderscoreTemplateLinter()]
    _process_os_walk('.', template_linters, options)


if __name__ == "__main__":
    main()
