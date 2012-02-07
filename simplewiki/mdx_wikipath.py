#!/usr/bin/env python

'''
WikiLink Extention for Python-Markdown
======================================

Converts CamelCase words to relative links.  Requires Python-Markdown 1.6+

Basic usage:

    >>> import markdown
    >>> text = "Some text with a WikiLink."
    >>> md = markdown.markdown(text, ['wikilink'])
    >>> md
    '\\n<p>Some text with a <a href="/WikiLink/" class="wikilink">WikiLink</a>.\\n</p>\\n\\n\\n'

To define custom settings the simple way:

    >>> md = markdown.markdown(text, 
    ...     ['wikilink(base_url=/wiki/,end_url=.html,html_class=foo)']
    ... )
    >>> md
    '\\n<p>Some text with a <a href="/wiki/WikiLink.html" class="foo">WikiLink</a>.\\n</p>\\n\\n\\n'
    
Custom settings the complex way:

    >>> md = markdown.Markdown(text, 
    ...     extensions = ['wikilink'], 
    ...     extension_configs = {'wikilink': [
    ...                                 ('base_url', 'http://example.com/'), 
    ...                                 ('end_url', '.html'),
    ...                                 ('html_class', '') ]},
    ...     encoding='utf8',
    ...     safe_mode = True)
    >>> str(md)
    '\\n<p>Some text with a <a href="http://example.com/WikiLink.html">WikiLink</a>.\\n</p>\\n\\n\\n'

Use MetaData with mdx_meta.py (Note the blank html_class in MetaData):

    >>> text = """wiki_base_url: http://example.com/
    ... wiki_end_url:     .html
    ... wiki_html_class:
    ... 
    ... Some text with a WikiLink."""
    >>> md = markdown.Markdown(text, ['meta', 'wikilink'])
    >>> str(md)
    '\\n<p>Some text with a <a href="http://example.com/WikiLink.html">WikiLink</a>.\\n</p>\\n\\n\\n'

From the command line:

    python markdown.py -x wikilink(base_url=http://example.com/,end_url=.html,html_class=foo) src.txt

By [Waylan Limberg](http://achinghead.com/).

Project website: http://achinghead.com/markdown-wikilinks/
Contact: waylan [at] gmail [dot] com

License: [BSD](http://www.opensource.org/licenses/bsd-license.php) 

Version: 0.4 (Oct 14, 2006)

Dependencies:
* [Python 2.3+](http://python.org)
* [Markdown 1.6+](http://www.freewisdom.org/projects/python-markdown/)
* For older dependencies use [WikiLink Version 0.3]
(http://code.limberg.name/svn/projects/py-markdown-ext/wikilinks/tags/release-0.3/)
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
                        'base_url' : ['/', 'String to append to beginning or URL.'],
                        'end_url' : ['/', 'String to append to end of URL.'],
                        'html_class' : ['wikipath', 'CSS hook. Leave blank for none.']
        }
        
        # Override defaults with user settings
        for key, value in configs :
            # self.config[key][0] = value
            self.setConfig(key, value)
                
                
    def extendMarkdown(self, md, md_globals):
        self.md = md
        
        # append to end of inline patterns
        WIKI_RE =  r'\[(?P<linkTitle>.+?)\]\(wiki:(?P<wikiTitle>[a-zA-Z\d/_-]*)\)'
        wikiPathPattern = WikiPath(WIKI_RE, self.getConfigs())
        wikiPathPattern.md = md
        md.inlinePatterns.add('wikipath', wikiPathPattern, "<reference")

class WikiPath(markdown.inlinepatterns.Pattern):
    def __init__(self, pattern, config):
        markdown.inlinepatterns.Pattern.__init__(self, pattern)
        self.config = config
    
    def handleMatch(self, m) :
        article_title = m.group('wikiTitle')
        if article_title.startswith("/"):
            article_title = article_title[1:]
        
        url = self.config['base_url'] + article_title
        label = m.group('linkTitle')
        a = etree.Element('a')
        a.set('href', url)
        a.text = label
        
        if self.config['html_class']:
            a.set('class', self.config['html_class'])
            
        return a
        
    def _getMeta(self):
        """ Return meta data or config data. """
        base_url = self.config['base_url']
        end_url = self.config['end_url']
        html_class = self.config['html_class']
        if hasattr(self.md, 'Meta'):
            if self.md.Meta.has_key('wiki_base_url'):
                base_url = self.md.Meta['wiki_base_url'][0]
            if self.md.Meta.has_key('wiki_end_url'):
                end_url = self.md.Meta['wiki_end_url'][0]
            if self.md.Meta.has_key('wiki_html_class'):
                html_class = self.md.Meta['wiki_html_class'][0]
        return base_url, end_url, html_class

def makeExtension(configs=None) :
    return WikiPathExtension(configs=configs)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
