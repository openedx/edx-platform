"""
Classes for Django Template Linting.
"""
from xsslint.utils import Expression, StringLines
from xsslint.reporting import ExpressionRuleViolation


class TransExpression(Expression):
    """
        The expression handling trans tag
    """

    def __init__(self, ruleset, *args, **kwargs):
        super(TransExpression, self).__init__(*args, **kwargs)
        self.string_lines = StringLines(kwargs['template'])
        self.ruleset = ruleset

    def validate_expression(self, template_file, results):
        """
        Validates trans tag expression for missing escaping filter

        Arguments:
            template_file: The content of the Django template.
            results: Violations to generated.

        Returns:
            None
        """

        trans_expr = self.expression_inner
        trans_expr_lineno = self.string_lines.index_to_line_number(self.start_index)
        if 'as' not in trans_expr:
            _add_violations(results, self.ruleset.django_trans_missing_escape, self)
            return

        pos = trans_expr.find('as')
        if pos == -1:
            _add_violations(results, self.ruleset.django_trans_missing_escape, self)
            return

        trans_var_name_used = trans_expr[pos + len('as'):].strip()
        escape_expr_start_pos = template_file.find('{{', self.end_index)
        if escape_expr_start_pos == -1:
            _add_violations(results,
                            self.ruleset.django_trans_missing_escape,
                            self)
            return

        # {{ found but should be on the same line as trans tag
        trans_expr_filter_lineno = self.string_lines.index_to_line_number(escape_expr_start_pos)
        if trans_expr_filter_lineno != trans_expr_lineno:
            _add_violations(results,
                            self.ruleset.django_trans_missing_escape,
                            self)
            return

        escape_expr_end_pos = template_file.find('}}', escape_expr_start_pos)
        # couldn't find matching }}
        if escape_expr_end_pos == -1:
            _add_violations(results,
                            self.ruleset.django_trans_missing_escape,
                            self)
            return

        # }} should be also on the same line
        trans_expr_filter_lineno = self.string_lines.index_to_line_number(escape_expr_end_pos)
        if trans_expr_filter_lineno != trans_expr_lineno:
            _add_violations(results,
                            self.ruleset.django_trans_missing_escape,
                            self)
            return

        escape_expr = template_file[escape_expr_start_pos + len('{{'):escape_expr_end_pos]
        # check escape expression has the right variable and its escaped properly
        # with force_escape filter
        if '|' not in escape_expr \
            or len(escape_expr.split('|')) != 2:
            _add_violations(results,
                            self.ruleset.django_trans_invalid_escape_filter,
                            self)
            return

        escape_expr_var_used, escape_filter = escape_expr.split('|')[0], escape_expr.split('|')[1]
        if trans_var_name_used != escape_expr_var_used:
            _add_violations(results,
                            self.ruleset.django_escape_variable_mismatch,
                            self)
            return

        if escape_filter != 'force_escape':
            _add_violations(results,
                            self.ruleset.django_trans_invalid_escape_filter,
                            self)
            return


class BlockTransExpression(Expression):
    """
        The expression handling blocktrans tag
    """
    def __init__(self, ruleset, *args, **kwargs):
        super(BlockTransExpression, self).__init__(*args, **kwargs)
        self.string_lines = StringLines(kwargs['template'])
        self.ruleset = ruleset

    def validate_expression(self, template_file, results):
        """
        Validates blocktrans tag expression for missing escaping filter

        Arguments:
            template_file: The content of the Django template.
            results: Violations generated.

        Returns:
            None
        """

        blocktrans_expr_lineno = self.string_lines.index_to_line_number(self.start_index)
        blocktrans_expr_column = self.string_lines.index_to_column_number(self.start_index)

        if blocktrans_expr_lineno == 0 and blocktrans_expr_column == 0:
            _add_violations(results,
                            self.ruleset.django_blocktrans_missing_escape_filter,
                            self)
            return
        if blocktrans_expr_lineno >= 0:
            filter_start_pos = template_file.rfind('{%', 0, self.start_index)
            if filter_start_pos == -1:
                _add_violations(results,
                                self.ruleset.django_blocktrans_missing_escape_filter,
                                self)
                return

            filter_end_pos = template_file.find('%}', filter_start_pos)
            if filter_end_pos > self.start_index:
                _add_violations(results,
                                self.ruleset.django_blocktrans_escape_filter_parse_error,
                                self)
                return

            escape_filter = template_file[filter_start_pos:filter_end_pos + 2]

            if len(escape_filter) < len('{%filter force_escape%}'):
                _add_violations(results,
                                self.ruleset.django_blocktrans_missing_escape_filter,
                                self)
                return

            escape_filter = escape_filter[2:-2].strip()
            escape_filter = escape_filter.split(' ')

            if len(escape_filter) != 2:
                _add_violations(results,
                                self.ruleset.django_bloctrans_invalid_escape_filter,
                                self)
                return

            if escape_filter[0] != 'filter' or escape_filter[1] != 'force_escape':
                _add_violations(results,
                                self.ruleset.django_bloctrans_invalid_escape_filter,
                                self)
                return

def _add_violations(results, rule_violation, self):
    results.violations.append(ExpressionRuleViolation(
        rule_violation, self
    ))
