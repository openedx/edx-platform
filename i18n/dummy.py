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
from __future__ import print_function
import re
import sys
import argparse

import polib
from path import path

from i18n.config import CONFIGURATION
from i18n.execute import create_dir_if_necessary
from i18n.converter import Converter


class BaseDummyConverter(Converter):
    """Base class for dummy converters.

    String conversion goes through a character map, then gets padded.

    """
    TABLE = {}

    def inner_convert_string(self, string):
        for old, new in self.TABLE.items():
            string = string.replace(old, new)
        return self.pad(string)

    def pad(self, string):
        return string

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


class Dummy(BaseDummyConverter):
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
    # Substitute plain characters with accented lookalikes.
    # http://tlt.its.psu.edu/suggestions/international/web/codehtml.html#accent
    TABLE = dict(zip(
        u"AabCcEeIiOoUuYy",
        u"ÀäßÇçÉéÌïÖöÛüÝý"
    ))

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

    def pad(self, string):
        """add some lorem ipsum text to the end of string"""
        size = len(string)
        if size < 7:
            target = size * 3
        else:
            target = int(size * self.PAD_FACTOR)
        pad_len = target - size - 1
        return string + self.LOREM[:pad_len] + "#"


class Dummy2(BaseDummyConverter):
    """A second dummy converter.

    Like Dummy, but uses a different obvious but readable automatic conversion:
    Strikes-through many letters, and turns lower-case letters upside-down.

    """
    TABLE = dict(zip(
        u"ABCDEGHIJKLOPRTUYZabcdefghijklmnopqrstuvwxyz",
        u"ȺɃȻĐɆǤĦƗɈꝀŁØⱣɌŦɄɎƵɐqɔpǝɟƃɥᴉɾʞlɯuødbɹsʇnʌʍxʎz"
    ))


def make_dummy(filename, locale, converter):
    """
    Takes a source po file, reads it, and writes out a new po file
    in :param locale: containing a dummy translation.
    """
    if not path(filename).exists():
        raise IOError('File does not exist: %r' % filename)
    pofile = polib.pofile(filename)
    for msg in pofile:
        # Some strings are actually formatting strings, don't dummy-ify them,
        # or dates will look like "DÀTÉ_TÌMÉ_FÖRMÀT Ⱡ'σ# EST"
        if re.match(r"^[A-Z_]+_FORMAT$", msg.msgid):
            continue
        converter.convert_msg(msg)

    # Apply declaration for English pluralization rules so that ngettext will
    # do something reasonable.
    pofile.metadata['Plural-Forms'] = 'nplurals=2; plural=(n != 1);'

    new_file = new_filename(filename, locale)
    create_dir_if_necessary(new_file)
    pofile.save(new_file)


def new_filename(original_filename, new_locale):
    """Returns a filename derived from original_filename, using new_locale as the locale"""
    f = path(original_filename)
    new_file = f.parent.parent.parent / new_locale / f.parent.name / f.name
    return new_file.abspath()


def main(verbosity=1):
    """
    Generate dummy strings for all source po files.
    """
    SOURCE_MSGS_DIR = CONFIGURATION.source_messages_dir
    for locale, converter in zip(CONFIGURATION.dummy_locales, [Dummy(), Dummy2()]):
        if verbosity:
            print('Processing source language files into dummy strings, locale "{}"'.format(locale))
        for source_file in CONFIGURATION.source_messages_dir.walkfiles('*.po'):
            if verbosity:
                print('   ', source_file.relpath())
            make_dummy(SOURCE_MSGS_DIR.joinpath(source_file), locale, converter)
    if verbosity:
        print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", "-v", action="count", default=0)
    args = parser.parse_args()
    ret = main(verbosity=args.verbose)
    sys.exit(ret)
