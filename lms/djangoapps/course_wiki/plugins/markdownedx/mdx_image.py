#!/usr/bin/env python
'''
Image Embedding Extension for Python-Markdown
======================================

Converts lone links to embedded images, provided the file extension is allowed.

Ex:
    http://www.ericfehse.net/media/img/ef/blog/django-pony.jpg
    becomes
    <img src="http://www.ericfehse.net/media/img/ef/blog/django-pony.jpg">

    mypic.jpg   becomes    <img src="/MEDIA_PATH/mypic.jpg">

Requires Python-Markdown 1.6+
'''

import simplewiki.settings as settings

import markdown
try:
    # Markdown 2.1.0 changed from 2.0.3. We try importing the new version first,
    # but import the 2.0.3 version if it fails
    from markdown.util import etree
except:
    from markdown import etree


class ImageExtension(markdown.Extension):
    def __init__(self, configs):
        for key, value in configs:
            self.setConfig(key, value)

    def add_inline(self, md, name, klass, re):
        pattern = klass(re)
        pattern.md = md
        pattern.ext = self
        md.inlinePatterns.add(name, pattern, "<reference")

    def extendMarkdown(self, md, md_globals):
        self.add_inline(md, 'image', ImageLink,
                        r'^(?P<proto>([^:/?#])+://)?(?P<domain>([^/?#]*)/)?(?P<path>[^?#]*\.(?P<ext>[^?#]{3,4}))(?:\?([^#]*))?(?:#(.*))?$')


class ImageLink(markdown.inlinepatterns.Pattern):
    def handleMatch(self, m):
        img = etree.Element('img')
        proto = m.group('proto') or "http://"
        domain = m.group('domain')
        path = m.group('path')
        ext = m.group('ext')

        # A fixer upper
        if ext.lower() in settings.WIKI_IMAGE_EXTENSIONS:
            if domain:
                src = proto + domain + path
            elif path:
                # We need a nice way to source local attachments...
                src = "/wiki/media/" + path + ".upload"
            else:
                src = ''
            img.set('src', src)
        return img


def makeExtension(configs=None):
    return ImageExtension(configs=configs)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
