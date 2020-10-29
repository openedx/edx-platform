"""
Utility classes/functions for the XSS Linter.
"""


import re


def is_skip_dir(skip_dirs, directory):
    """
    Determines whether a directory should be skipped or linted.

    Arguments:
        skip_dirs: The configured directories to be skipped.
        directory: The current directory to be tested.

    Returns:
         True if the directory should be skipped, and False otherwise.

    """
    for skip_dir in skip_dirs:
        skip_dir_regex = re.compile(
            "(.*/)*{}(/.*)*".format(re.escape(skip_dir)))
        if skip_dir_regex.match(directory) is not None:
            return True
    return False


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
