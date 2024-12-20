"""
Helper class to convert mathjax equations to plain text.
"""

import re

import unicodeit


class PlainTextMath:
    """
    Converts mathjax equations to plain text using unicodeit and some preprocessing.
    """
    equation_pattern = re.compile(
        r'\[mathjaxinline\](.*?)\[\/mathjaxinline\]|\[mathjax\](.*?)\[\/mathjax\]|\\\((.*?)\\\)|\\\[(.*?)\\\]'
    )
    eqn_replacements = (
        # just remove prefix `\`
        ("\\sin", "sin"),
        ("\\cos", "cos"),
        ("\\tan", "tan"),
        ("\\arcsin", "arcsin"),
        ("\\arccos", "arccos"),
        ("\\arctan", "arctan"),
        ("\\cot", "cot"),
        ("\\sec", "sec"),
        ("\\csc", "csc"),
        # Is used for matching brackets in mathjax, should not be required in plain text.
        ("\\left", ""),
        ("\\right", ""),
    )
    regex_replacements = (
        (re.compile(r'\\mathbf{(.*?)}'), r"\1"),
    )

    def _fraction_handler(self, equation: str) -> str:
        """
        Converts `\\frac{x}{y}` to `(x/y)` while handling nested `{}`.

        For example: `\\frac{2}{\\sqrt{1+y}}` is converted to `(2/\\sqrt{1+y})`.

        Args:
            equation: string

        Returns:
            String with `\\frac` replaced by normal `/` symbol.
        """
        start_index = equation.find("\\frac{")
        if start_index == -1:
            return equation
        mid_index = equation.find("}{")
        if mid_index == -1:
            return equation

        numerator = equation[start_index + 6:mid_index]
        # shift mid_index by length of }{ chars i.e., 2
        mid_index += 2
        open_count = 0

        for i, char in enumerate(equation[mid_index:]):
            if char == "{":
                open_count += 1
            if char == "}":
                if open_count == 0:
                    break
                open_count -= 1
        else:
            # Invalid `\frac` format
            return equation

        denominator = equation[mid_index:mid_index + i]
        # Now re-create the equation with `(numerator / denominator)`
        equation = equation[:start_index] + f"({numerator}/{denominator})" + equation[mid_index + i + 1:]
        return equation

    def _handle_replacements(self, equation: str) -> str:
        """
        Makes a bunch of replacements in equation string.
        """
        for q, replacement in self.eqn_replacements:
            equation = equation.replace(q, replacement)
        for pattern, replacement in self.regex_replacements:
            equation = re.sub(pattern, replacement, equation)
        return equation

    def run(self, eqn_matches: re.Match) -> str:
        """
        Takes re.Match object and runs conversion process on each match group.
        """
        groups = eqn_matches.groups()
        for group in groups:
            if group:
                group = self._fraction_handler(group)
                group = self._handle_replacements(group)
                return unicodeit.replace(group)
        return None


processor = PlainTextMath()


def process_mathjax(content: str) -> str:
    return re.sub(processor.equation_pattern, processor.run, content)
