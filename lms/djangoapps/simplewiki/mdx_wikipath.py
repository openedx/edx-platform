#!/usr/bin/env python

'''
Wikipath Extension for Python-Markdown
======================================

Converts [Link Name](wiki:ArticleName) to relative links pointing to article.  Requires Python-Markdown 2.0+

Basic usage:

    >>> import markdown
    >>> text = "Some text with a [Link Name](wiki:ArticleName)."
    >>> html = markdown.markdown(text, ['wikipath(base_url="/wiki/view/")'])
    >>> html
    u'<p>Some text with a <a class="wikipath" href="/wiki/view/ArticleName/">Link Name</a>.</p>'

Dependencies:
* [Python 2.3+](http://python.org)
* [Markdown 2.0+](http://www.freewisdom.org/projects/python-markdown/)
'''


import markdown
try:
    # Markdown 2.1.0 changed from 2.0.3. We try importing the new version first,
    # but import the 2.0.3 version if it fails
    from markdown.util import etree
except:
    from markdown import etree


class WikiPathExtension(markdown.Extension):
    def __init__(self, configs):
        # set extension defaults
        self.config = {
                        'default_namespace': ['edX', 'Default namespace for when one isn\'t specified.'],
                        'html_class': ['wikipath', 'CSS hook. Leave blank for none.']
        }

        # Override defaults with user settings
        for key, value in configs:
            # self.config[key][0] = value
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        self.md = md

        # append to end of inline patterns
        WIKI_RE = r'\[(?P<linkTitle>.+?)\]\(wiki:(?P<wikiTitle>[a-zA-Z\d/_-]*)\)'
        wikiPathPattern = WikiPath(WIKI_RE, self.config)
        wikiPathPattern.md = md
        md.inlinePatterns.add('wikipath', wikiPathPattern, "<reference")


class WikiPath(markdown.inlinepatterns.Pattern):
    def __init__(self, pattern, config):
        markdown.inlinepatterns.Pattern.__init__(self, pattern)
        self.config = config

    def handleMatch(self, m):
        article_title = m.group('wikiTitle')
        if article_title.startswith("/"):
            article_title = article_title[1:]

        if not "/" in article_title:
            article_title = self.config['default_namespace'][0] + "/" + article_title

        url = "../" + article_title
        label = m.group('linkTitle')
        a = etree.Element('a')
        a.set('href', url)
        a.text = label

        if self.config['html_class'][0]:
            a.set('class', self.config['html_class'][0])

        return a

    def _getMeta(self):
        """ Return meta data or config data. """
        base_url = self.config['base_url'][0]
        html_class = self.config['html_class'][0]
        if hasattr(self.md, 'Meta'):
            if self.md.Meta.has_key('wiki_base_url'):
                base_url = self.md.Meta['wiki_base_url'][0]
            if self.md.Meta.has_key('wiki_html_class'):
                html_class = self.md.Meta['wiki_html_class'][0]
        return base_url, html_class


def makeExtension(configs=None):
    return WikiPathExtension(configs=configs)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
