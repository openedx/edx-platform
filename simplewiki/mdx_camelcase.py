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

class CamelCaseExtension(markdown.Extension):
    def __init__(self, configs):
        # set extension defaults
        self.config = {
                        'base_url' : ['/', 'String to append to beginning or URL.'],
                        'end_url' : ['/', 'String to append to end of URL.'],
                        'html_class' : ['wikilink', 'CSS hook. Leave blank for none.']
        }
        
        # Override defaults with user settings
        for key, value in configs :
            # self.config[key][0] = value
            self.setConfig(key, value)
    
    def add_inline(self, md, name, klass, re):
        pattern = klass(re)
        pattern.md = md
        pattern.ext = self
        md.inlinePatterns.add(name, pattern, "<reference")
    
    def extendMarkdown(self, md, md_globals):
        self.add_inline(md, 'camel', CamelCaseLinks, 
                  r'''(?P<escape>\\|\b)(?P<camelcase>([A-Z]+[a-z-_]+){2,})(?:"")?\b''')

class CamelCaseLinks(markdown.inlinepatterns.Pattern):
    def handleMatch(self, m) :
        if  m.group('escape') == '\\':
            a = markdown.etree.Element('a')#doc.createTextNode(m.group('camelcase'))
        else :
            url = m.group('camelcase')
                             #'%s%s%s'% (self.md.wiki_config['base_url'][0], \
                             #m.group('camelcase'), \
                             #self.md.wiki_config['end_url'][0])
            label = m.group('camelcase').replace('_', ' ')
            a = markdown.etree.Element('a')
            a.set('href', url)
            a.text = label
        a.set('class', 'wikilink')
        return a
    
class CamelCasePreprocessor(markdown.preprocessors.Preprocessor) :
    
    def run(self, lines) :
        '''
        Updates WikiLink Extension configs with Meta Data.
        Passes "lines" through unchanged.
        
        Run as a preprocessor because must run after the 
        MetaPreprocessor runs and only needs to run once.
        '''
        if hasattr(self.md, 'Meta'):
            if self.md.Meta.has_key('wiki_base_url'):
                self.md.wiki_config['base_url'][0] = self.md.Meta['wiki_base_url'][0]
            if self.md.Meta.has_key('wiki_end_url'):
                self.md.wiki_config['end_url'][0] = self.md.Meta['wiki_end_url'][0]
            if self.md.Meta.has_key('wiki_html_class'):
                self.md.wiki_config['html_class'][0] = self.md.Meta['wiki_html_class'][0]
        
        return lines

def makeExtension(configs=None) :
    return CamelCaseExtension(configs=configs)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
