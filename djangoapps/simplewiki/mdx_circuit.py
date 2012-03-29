#!/usr/bin/env python
'''
Image Circuit Extension for Python-Markdown
======================================

circuit:name becomes the circuit. 
'''
import markdown
import re

import simplewiki.settings as settings

from django.utils.html import escape
from mitxmako.shortcuts import render_to_response, render_to_string


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
            
    
    def extendMarkdown(self, md, md_globals):
        ## Because Markdown treats contigous lines as one block of text, it is hard to match
        ## a regex that must occupy the whole line (like the circuit regex). This is why we have
        ## a preprocessor that inspects the lines and replaces the matched lines with text that is
        ## easier to match
        md.preprocessors.add('circuit',  CircuitPreprocessor(md), "_begin")
        
        pattern = CircuitLink(r'processed-schematic:(?P<data>.*?)processed-schematic-end')
        pattern.md = md
        pattern.ext = self
        md.inlinePatterns.add('circuit', pattern, "<reference")


class CircuitPreprocessor(markdown.preprocessors.Preprocessor):
    preRegex = re.compile(r'^circuit-schematic:(?P<data>.*)$')
    
    def run(self, lines):
            new_lines = []
            for line in lines:
                m = self.preRegex.match(line)
                if m:
                    new_lines.append('processed-schematic:{0}processed-schematic-end'.format( m.group('data') ))
                else:
                    new_lines.append(line)
            return new_lines


class CircuitLink(markdown.inlinepatterns.Pattern):
    def handleMatch(self, m):
        data = m.group('data')
        data = escape(data)
        ##TODO: We need to html escape the data
        return etree.fromstring("<div align='center'><input type='hidden' parts='' value='" + data + "' analyses='' class='schematic ctrls' width='500' height='300'/></div>")
        
    
def makeExtension(configs=None) :
    return CircuitExtension(configs=configs)
