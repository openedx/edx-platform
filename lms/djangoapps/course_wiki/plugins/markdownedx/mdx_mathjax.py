# Source: https://github.com/mayoff/python-markdown-mathjax  # lint-amnesty, pylint: disable=missing-module-docstring


import markdown

try:
    # Markdown 2.1.0 changed from 2.0.3. We try importing the new version first,
    # but import the 2.0.3 version if it fails
    from markdown.util import etree, AtomicString
except:  # lint-amnesty, pylint: disable=bare-except
    from markdown import etree, AtomicString


class MathJaxPattern(markdown.inlinepatterns.Pattern):  # lint-amnesty, pylint: disable=missing-class-docstring

    def __init__(self):
        markdown.inlinepatterns.Pattern.__init__(self, r'(?<!\\)(\$\$?)(.+?)\2')

    def handleMatch(self, m):
        el = etree.Element('span')
        el.text = AtomicString(m.group(2) + m.group(3) + m.group(2))
        return el


class MathJaxExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):  # lint-amnesty, pylint: disable=arguments-differ, unused-argument
        # Needs to come before escape matching because \ is pretty important in LaTeX
        md.inlinePatterns.add('mathjax', MathJaxPattern(), '<escape')


def makeExtension(**kwargs):
    return MathJaxExtension(**kwargs)
