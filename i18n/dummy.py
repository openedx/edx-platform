# -*- coding: iso-8859-15 -*-

from converter import Converter

# This file converts string resource files.
#   Java: file has name like messages_en.properties
#   Flex: file has name like locales/en_US/Labels.properties

# Creates new localization properties files in a dummy language (saved as 'vr', Vardebedian)
# Each property file is derived from the equivalent en_US file, except
# 1. Every vowel is replaced with an equivalent with extra accent marks
# 2. Every string is padded out to +30% length to simulate verbose languages (e.g. German)
#    to see if layout and flows work properly
# 3. Every string is terminated with a '#' character to make it easier to detect truncation


# --------------------------------
# Example use:
# >>> from dummy import Dummy
# >>> c = Dummy()
# >>> print c.convert("hello my name is Bond, James Bond")
# héllö my nämé ïs Bönd, Jämés Bönd Lorem i#
#
# >>> print c.convert('don\'t convert <a href="href">tag ids</a>')
# dön't çönvért <a href="href">täg ïds</a> Lorem ipsu#
#
# >>> print c.convert('don\'t convert %(name)s tags on %(date)s')
# dön't çönvért %(name)s tags on %(date)s Lorem ips#


# Substitute plain characters with accented lookalikes.
# http://tlt.its.psu.edu/suggestions/international/web/codehtml.html#accent
# print "print u'\\x%x'" % 207
TABLE = {'A': u'\xC0',
         'a': u'\xE4',
         'b': u'\xDF',
         'C': u'\xc7',
         'c': u'\xE7',
         'E': u'\xC9',
         'e': u'\xE9',
         'I': U'\xCC',
         'i': u'\xEF',
         'O': u'\xD8',
         'o': u'\xF6',
         'u': u'\xFC'
         }



# The print industry's standard dummy text, in use since the 1500s
# see http://www.lipsum.com/
LOREM = ' Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed ' \
        'do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad ' \
        'minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ' \
        'ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate ' \
        'velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat ' \
        'cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. '

# To simulate more verbose languages (like German), pad the length of a string
# by a multiple of PAD_FACTOR
PAD_FACTOR = 1.3


class Dummy (Converter):
    '''
    A string converter that generates dummy strings with fake accents
    and lorem ipsum padding.
    '''

    def convert (self, string):
        result = Converter.convert(self, string)
        return self.pad(result)

    def inner_convert_string (self, string):
        for (k,v) in TABLE.items():
            string = string.replace(k, v)
        return string


    def pad (self, string):
        '''add some lorem ipsum text to the end of string'''
        size = len(string)
        if size < 7:
            target = size*3
        else:
            target = int(size*PAD_FACTOR)
        return string + self.terminate(LOREM[:(target-size)])

    def terminate (self, string):
        '''replaces the final char of string with #'''
        return string[:-1]+'#'

    def init_msgs (self, msgs):
        '''
        Make sure the first msg in msgs has a plural property.
        msgs is list of instances of pofile.Msg
        '''
        if len(msgs)==0:
            return
        headers = msgs[0].get_property('msgstr')
        has_plural = len([header for header in headers if header.find('Plural-Forms:') == 0])>0
        if not has_plural:
            # Apply declaration for English pluralization rules
            plural = "Plural-Forms: nplurals=2; plural=(n != 1);\\n"
            headers.append(plural)
        

    def convert_msg (self, msg):
        '''
        Takes one Msg object and converts it (adds a dummy translation to it)
        msg is an instance of pofile.Msg
        '''
        source = msg.get_property('msgid')
        if len(source)==1 and len(source[0])==0:
            # don't translate empty string
            return
        plural = msg.get_property('msgid_plural')
        if len(plural)>0:
            # translate singular and plural
            foreign_single = self.convert(merge(source))
            foreign_plural = self.convert(merge(plural))
            msg.set_property('msgstr[0]', split(foreign_single))
            msg.set_property('msgstr[1]', split(foreign_plural))
            return
        else:
            src_merged = merge(source)
            foreign = self.convert(src_merged)
            if len(source)>1:
                # If last char is a newline, make sure translation
                # has a newline too.
                if src_merged[-2:]=='\\n':
                    foreign += '\\n'
            msg.set_property('msgstr', split(foreign))


# ----------------------------------
# String splitting utility functions

SPLIT_SIZE = 70

def merge (string_list):
    '''returns a single string: concatenates string_list'''
    return ''.join(string_list)

# .po file format requires long strings to be broken
# up into several shorter (<80 char) strings.
# The first string is empty (""), which indicates
# that more are to be read on following lines.

def split (string):
    '''
    Returns string split into fragments of a given size.
    If there are multiple fragments, insert "" as the first fragment.
    '''
    result = [chunk for chunk in chunks(string, SPLIT_SIZE)]
    if len(result)>1:
        result = [''] + result
    return result

def chunks(string, size):
    '''
    Generate fragments of a given size from string. Avoid breaking
    the string in the middle of an escape sequence (e.g. "\n")
    '''
    strlen=len(string)-1
    esc = False
    last = 0
    for i,char in enumerate(string):
        if not esc and char == '\\':
            esc = True
            continue
        if esc:
            esc = False
        if i>=last+size-1 or i==strlen:
            chunk = string[last:i+1]
            last = i+1
            yield chunk

# testing
# >>> a = "abcd\\efghijklmnopqrstuvwxyz"
# >>> SPLIT_SIZE = 5
# >>> split(a)
# ['abcd\\e', 'fghij', 'klmno', 'pqrst', 'uvwxy', 'z']
# >>> merge(split(a))
# 'abcd\\efghijklmnopqrstuvwxyz'

