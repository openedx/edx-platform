# -*- coding: utf-8 -*-
"""Markdown filters with mistune

Used from markdown.py
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import re
import cgi

import mistune

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from nbconvert.filters.strings import add_anchor


class MathBlockGrammar(mistune.BlockGrammar):
    """This defines a single regex comprised of the different patterns that 
    identify math content spanning multiple lines. These are used by the 
    MathBlockLexer.
    """
    multi_math_str = "|".join([r"^\$\$.*?\$\$",
                               r"^\\\\\[.*?\\\\\]",
                               r"^\\begin\{([a-z]*\*?)\}(.*?)\\end\{\1\}"])
    multiline_math = re.compile(multi_math_str, re.DOTALL)


class MathBlockLexer(mistune.BlockLexer):
    """ This acts as a pass-through to the MathInlineLexer. It is needed in 
    order to avoid other block level rules splitting math sections apart. 
    """
    
    default_rules = (['multiline_math']
                     + mistune.BlockLexer.default_rules)

    def __init__(self, rules=None, **kwargs):
        if rules is None:
            rules = MathBlockGrammar()
        super(MathBlockLexer, self).__init__(rules, **kwargs)

    def parse_multiline_math(self, m):
        """Add token to pass through mutiline math."""
        self.tokens.append({
            "type": "multiline_math",
            "text": m.group(0)
        })


class MathInlineGrammar(mistune.InlineGrammar):
    """This defines different ways of declaring math objects that should be 
    passed through to mathjax unaffected. These are used by the MathInlineLexer.
    """
    inline_math = re.compile(r"^\$(.+?)\$|^\\\\\((.+?)\\\\\)", re.DOTALL)
    block_math = re.compile(r"^\$\$(.*?)\$\$|^\\\\\[(.*?)\\\\\]", re.DOTALL)
    latex_environment = re.compile(r"^\\begin\{([a-z]*\*?)\}(.*?)\\end\{\1\}",
                                   re.DOTALL)
    text = re.compile(r'^[\s\S]+?(?=[\\<!\[_*`~$]|https?://| {2,}\n|$)')


class MathInlineLexer(mistune.InlineLexer):
    """This interprets the content of LaTeX style math objects using the rules 
    defined by the MathInlineGrammar. 
    
    In particular this grabs ``$$...$$``, ``\\[...\\]``, ``\\(...\\)``, ``$...$``, 
    and ``\begin{foo}...\end{foo}`` styles for declaring mathematics. It strips 
    delimiters from all these varieties, and extracts the type of environment 
    in the last case (``foo`` in this example).
    """
    default_rules = (['block_math', 'inline_math', 'latex_environment']
                     + mistune.InlineLexer.default_rules)

    def __init__(self, renderer, rules=None, **kwargs):
        if rules is None:
            rules = MathInlineGrammar()
        super(MathInlineLexer, self).__init__(renderer, rules, **kwargs)

    def output_inline_math(self, m):
        return self.renderer.inline_math(m.group(1) or m.group(2))

    def output_block_math(self, m):
        return self.renderer.block_math(m.group(1) or m.group(2) or "")

    def output_latex_environment(self, m):
        return self.renderer.latex_environment(m.group(1),
                                               m.group(2))


class MarkdownWithMath(mistune.Markdown):
    def __init__(self, renderer, **kwargs):
        if 'inline' not in kwargs:
            kwargs['inline'] = MathInlineLexer
        if 'block' not in kwargs:
            kwargs['block'] = MathBlockLexer
        super(MarkdownWithMath, self).__init__(renderer, **kwargs)

    
    def output_multiline_math(self):
        return self.inline(self.token["text"])


class IPythonRenderer(mistune.Renderer):
    def block_code(self, code, lang):
        if lang:
            try:
                lexer = get_lexer_by_name(lang, stripall=True)
            except ClassNotFound:
                code = lang + '\n' + code
                lang = None

        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code)

        formatter = HtmlFormatter()
        return highlight(code, lexer, formatter)

    def header(self, text, level, raw=None):
        html = super(IPythonRenderer, self).header(text, level, raw=raw)
        anchor_link_text = self.options.get('anchor_link_text', u'¶')
        return add_anchor(html, anchor_link_text=anchor_link_text)

    # We must be careful here for compatibility
    # html.escape() is not availale on python 2.7
    # For more details, see:
    # https://wiki.python.org/moin/EscapingHtml
    def escape_html(self, text):
        return cgi.escape(text)

    def block_math(self, text):
        return '$$%s$$' % self.escape_html(text)

    def latex_environment(self, name, text):
        name = self.escape_html(name)
        text = self.escape_html(text)
        return r'\begin{%s}%s\end{%s}' % (name, text, name)

    def inline_math(self, text):
        return '$%s$' % self.escape_html(text)


def markdown2html_mistune(source):
    """Convert a markdown string to HTML using mistune"""
    return MarkdownWithMath(renderer=IPythonRenderer(
        escape=False)).render(source)
