#!/usr/bin/env python
'''
Image Circuit Extension for Python-Markdown
======================================

circuit:name becomes the circuit. 
'''

import simplewiki.settings as settings

from mitxmako.shortcuts import render_to_response, render_to_string

import markdown
try:
    # Markdown 2.1.0 changed from 2.0.3. We try importing the new version first,
    # but import the 2.0.3 version if it fails
    from markdown.util import etree
except:
    from markdown import etree

class CircuitExtension(markdown.Extension):
    def __init__(self, configs):
        for key, value in configs :
            self.setConfig(key, value)
    
    def add_inline(self, md, name, klass, re):
        pattern = klass(re)
        pattern.md = md
        pattern.ext = self
        md.inlinePatterns.add(name, pattern, "<reference")
    
    def extendMarkdown(self, md, md_globals):
        self.add_inline(md, 'circuit', CircuitLink, r'^circuit-schematic:(?P<data>.*)$')

class CircuitLink(markdown.inlinepatterns.Pattern):
    def handleMatch(self, m):
        data = m.group('data')
        
        ##TODO: We need to html escape the data
        return etree.fromstring("<input type='hidden' parts='' value='" + data + "' analyses='' class='schematic ctrls'/>")
        
    
def makeExtension(configs=None) :
    return CircuitExtension(configs=configs)
