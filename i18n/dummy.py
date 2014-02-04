#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generate test translation files from human-readable po files.

Dummy language is specified in configuration file (see config.py)
two letter language codes reference:
see http://www.loc.gov/standards/iso639-2/php/code_list.php

Django will not localize in languages that django itself has not been
localized for. So we are using a well-known language (default='eo').
Django languages are listed in django.conf.global_settings.LANGUAGES

po files can be generated with this:
django-admin.py makemessages --all --extension html -l en

Usage:

$ ./dummy.py

generates output conf/locale/$DUMMY_LOCALE/LC_MESSAGES,
where $DUMMY_LOCALE is the dummy_locale value set in the i18n config
"""

import sys
import os
import polib

from i18n.config import CONFIGURATION
from i18n.execute import create_dir_if_necessary
from i18n.converter import Converter

# Substitute plain characters with accented lookalikes.
# http://tlt.its.psu.edu/suggestions/international/web/codehtml.html#accent
TABLE = {
    'A': u'À',
    'a': u'ä',
    'b': u'ß',
    'C': u'Ç',
    'c': u'ç',
    'E': u'É',
    'e': u'é',
    'I': u'Ì',
    'i': u'ï',
    'O': u'Ø',
    'o': u'ø',
    'U': u'Û',
    'u': u'ü',
    'Y': u'Ý',
    'y': u'ý',
}


# The print industry's standard dummy text, in use since the 1500s
# see http://www.lipsum.com/, then fed through a "fancy-text" converter.
# The string should start with a space, so that it joins nicely with the text
# that precedes it.  The Lorem contains an apostrophe since French often does,
# and translated strings get put into single-quoted strings, which then break.
LOREM = " " + " ".join(     # join and split just make the string easier here.
    u"""
    Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢тєтυя α∂ιριѕι¢ιηg єłιт, ѕє∂ ∂σ єιυѕмσ∂
    тємρσя ιη¢ι∂ι∂υηт υт łαвσяє єт ∂σłσяє мαgηα αłιqυα. υт єηιм α∂ мιηιм
    νєηιαм, qυιѕ ησѕтяυ∂ єχєя¢ιтαтιση υłłαм¢σ łαвσяιѕ ηιѕι υт αłιqυιρ єχ єα
    ¢σммσ∂σ ¢σηѕєqυαт.  ∂υιѕ αυтє ιяυяє ∂σłσя ιη яєρяєнєη∂єяιт ιη νσłυρтαтє
    νєłιт єѕѕє ¢ιłłυм ∂σłσяє єυ ƒυgιαт ηυłłα ραяιαтυя. єχ¢єρтєυя ѕιηт σ¢¢αє¢αт
    ¢υρι∂αтαт ηση ρяσι∂єηт, ѕυηт ιη ¢υłρα qυι σƒƒι¢ια ∂єѕєяυηт мσłłιт αηιм ι∂
    єѕт łαвσяυм.
    """.split()
)

# To simulate more verbose languages (like German), pad the length of a string
# by a multiple of PAD_FACTOR
PAD_FACTOR = 1.33


class Dummy(Converter):
    r"""
    Creates new localization properties files in a dummy language.

    Each property file is derived from the equivalent en_US file, with these
    transformations applied:

    1. Every vowel is replaced with an equivalent with extra accent marks.

    2. Every string is padded out to +30% length to simulate verbose languages
       (such as German) to see if layout and flows work properly.

    3. Every string is terminated with a '#' character to make it easier to detect
       truncation.

    Example use::

        >>> from dummy import Dummy
        >>> c = Dummy()
        >>> c.convert("My name is Bond, James Bond")
        u'M\xfd n\xe4m\xe9 \xefs B\xf8nd, J\xe4m\xe9s B\xf8nd \u2360\u03c3\u044f\u0454\u043c \u03b9\u03c1#'
        >>> print c.convert("My name is Bond, James Bond")
        Mý nämé ïs Bønd, Jämés Bønd Ⱡσяєм ιρ#
        >>> print c.convert("don't convert <a href='href'>tag ids</a>")
        døn't çønvért <a href='href'>täg ïds</a> Ⱡσяєм ιρѕυ#
        >>> print c.convert("don't convert %(name)s tags on %(date)s")
        døn't çønvért %(name)s tägs øn %(date)s Ⱡσяєм ιρѕ#
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
            plural = {
                '0': self.final_newline(source, foreign_single),
                '1': self.final_newline(plural, foreign_plural),
            }
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


def make_dummy(file, locale):
    """
    Takes a source po file, reads it, and writes out a new po file
    in :param locale: containing a dummy translation.
    """
    if not os.path.exists(file):
        raise IOError('File does not exist: %s' % file)
    pofile = polib.pofile(file)
    converter = Dummy()
    for msg in pofile:
        converter.convert_msg(msg)

    # Apply declaration for English pluralization rules so that ngettext will
    # do something reasonable.
    pofile.metadata['Plural-Forms'] = 'nplurals=2; plural=(n != 1);'

    new_file = new_filename(file, locale)
    create_dir_if_necessary(new_file)
    pofile.save(new_file)


def new_filename(original_filename, new_locale):
    """Returns a filename derived from original_filename, using new_locale as the locale"""
    orig_dir = os.path.dirname(original_filename)
    msgs_dir = os.path.basename(orig_dir)
    orig_file = os.path.basename(original_filename)
    return os.path.abspath(os.path.join(orig_dir, '../..', new_locale, msgs_dir, orig_file))


def main():
    """
    Generate dummy strings for all source po files.
    """
    LOCALE = CONFIGURATION.dummy_locale
    SOURCE_MSGS_DIR = CONFIGURATION.source_messages_dir
    print "Processing source language files into dummy strings:"
    for source_file in CONFIGURATION.source_messages_dir.walkfiles('*.po'):
        print '   ', source_file.relpath()
        make_dummy(SOURCE_MSGS_DIR.joinpath(source_file), LOCALE)
    print


if __name__ == '__main__':
    sys.exit(main())
