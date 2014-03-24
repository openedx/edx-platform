#!/usr/bin/env python
'''
Image Circuit Extension for Python-Markdown
======================================


Any single line beginning with circuit-schematic: and followed by data (which should be json data, but this
is not enforced at this level) will be displayed as a circuit schematic. This is simply an input element with
the value set to the data. It is left to javascript on the page to render that input as a circuit schematic.

ex:
circuit-schematic:[["r",[128,48,0],{"r":"1","_json_":0},["2","1"]],["view",0,0,2,null,null,null,null,null,null,null],["dc",{"0":0,"1":1,"I(_3)":-1}]]

(This is a schematic with a single one-ohm resistor. Note that this data is not meant to be user-editable.)

'''
import markdown
import re

from django.utils.html import escape

try:
    # Markdown 2.1.0 changed from 2.0.3. We try importing the new version first,
    # but import the 2.0.3 version if it fails
    from markdown.util import etree
except:
    from markdown import etree


class CircuitExtension(markdown.Extension):
    def __init__(self, configs):
        for key, value in configs:
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        ## Because Markdown treats contigous lines as one block of text, it is hard to match
        ## a regex that must occupy the whole line (like the circuit regex). This is why we have
        ## a preprocessor that inspects the lines and replaces the matched lines with text that is
        ## easier to match
        md.preprocessors.add('circuit', CircuitPreprocessor(md), "_begin")

        pattern = CircuitLink(r'processed-schematic:(?P<data>.*?)processed-schematic-end')
        pattern.md = md
        pattern.ext = self
        md.inlinePatterns.add('circuit', pattern, "<reference")


class CircuitPreprocessor(markdown.preprocessors.Preprocessor):
    preRegex = re.compile(r'^circuit-schematic:(?P<data>.*)$')

    def run(self, lines):
        def convertLine(line):
            m = self.preRegex.match(line)
            if m:
                return 'processed-schematic:{0}processed-schematic-end'.format(m.group('data'))
            else:
                return line

        return [convertLine(line) for line in lines]


class CircuitLink(markdown.inlinepatterns.Pattern):
    def handleMatch(self, m):
        data = m.group('data')
        data = escape(data)
        return etree.fromstring("<div align='center'><input type='hidden' parts='' value='" + data + "' analyses='' class='schematic ctrls' width='400' height='220'/></div>")


def makeExtension(configs=None):
    to_return = CircuitExtension(configs=configs)
    return to_return
