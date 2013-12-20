from converter import Converter

# Creates new localization properties files in a dummy language
# Each property file is derived from the equivalent en_US file, except
# 1. Every vowel is replaced with an equivalent with extra accent marks
# 2. Every string is padded out to +30% length to simulate verbose languages (e.g. German)
#    to see if layout and flows work properly
# 3. Every string is terminated with a '#' character to make it easier to detect truncation


# --------------------------------
# Example use:
# >>> from dummy import Dummy
# >>> c = Dummy()
# >>> c.convert("hello my name is Bond, James Bond")
# u'h\xe9ll\xf6 my n\xe4m\xe9 \xefs B\xf6nd, J\xe4m\xe9s B\xf6nd Lorem i#'
#
# >>> c.convert('don\'t convert <a href="href">tag ids</a>')
# u'd\xf6n\'t \xe7\xf6nv\xe9rt <a href="href">t\xe4g \xefds</a> Lorem ipsu#'
#
# >>> c.convert('don\'t convert %(name)s tags on %(date)s')
# u"d\xf6n't \xe7\xf6nv\xe9rt %(name)s t\xe4gs \xf6n %(date)s Lorem ips#"


# Substitute plain characters with accented lookalikes.
# http://tlt.its.psu.edu/suggestions/international/web/codehtml.html#accent
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


class Dummy(Converter):
    """
    A string converter that generates dummy strings with fake accents
    and lorem ipsum padding.

    """
    def convert(self, string):
        result = Converter.convert(self, string)
        return self.pad(result)

    def inner_convert_string(self, string):
        for k, v in TABLE.items():
            string = string.replace(k, v)
        return string

    def pad(self, string):
        """add some lorem ipsum text to the end of string"""
        size = len(string)
        if size < 7:
            target = size * 3
        else:
            target = int(size*PAD_FACTOR)
        return string + self.terminate(LOREM[:(target-size)])

    def terminate(self, string):
        """replaces the final char of string with #"""
        return string[:-1] + '#'

    def init_msgs(self, msgs):
        """
        Make sure the first msg in msgs has a plural property.
        msgs is list of instances of polib.POEntry
        """
        if not msgs:
            return
        headers = msgs[0].get_property('msgstr')
        has_plural = any(header.startswith('Plural-Forms:') for header in headers)
        if not has_plural:
            # Apply declaration for English pluralization rules
            plural = "Plural-Forms: nplurals=2; plural=(n != 1);\\n"
            headers.append(plural)

    def convert_msg(self, msg):
        """
        Takes one POEntry object and converts it (adds a dummy translation to it)
        msg is an instance of polib.POEntry
        """
        source = msg.msgid
        if not source:
            # don't translate empty string
            return

        plural = msg.msgid_plural
        if plural:
            # translate singular and plural
            foreign_single = self.convert(source)
            foreign_plural = self.convert(plural)
            plural = {'0': self.final_newline(source, foreign_single),
                      '1': self.final_newline(plural, foreign_plural)}
            msg.msgstr_plural = plural
        else:
            foreign = self.convert(source)
            msg.msgstr = self.final_newline(source, foreign)

    def final_newline(self, original, translated):
        """ Returns a new translated string.
            If last char of original is a newline, make sure translation
            has a newline too.
        """
        if original:
            if original[-1] == '\n' and translated[-1] != '\n':
                translated += '\n'
        return translated
