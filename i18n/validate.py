"""Tests that validate .po files."""

import argparse
import codecs
import logging
import os
import sys
import textwrap

import polib

from i18n.config import LOCALE_DIR
from i18n.execute import call
from i18n.converter import Converter


log = logging.getLogger(__name__)

def validate_po_files(root, report_empty=False):
    """
    Validate all of the po files found in the root directory.
    """

    for dirpath, __, filenames in os.walk(root):
        for name in filenames:
            __, ext = os.path.splitext(name)
            if ext.lower() == '.po':
                filename = os.path.join(dirpath, name)
                # First validate the format of this file
                msgfmt_check_po_file(filename)
                # Now, check that the translated strings are valid, and optionally check for empty translations
                check_messages(filename, report_empty)


def msgfmt_check_po_file(filename):
    """
    Call GNU msgfmt -c on each .po file to validate its format.
    Any errors caught by msgfmt are logged to log.
    """
    # Use relative paths to make output less noisy.
    rfile = os.path.relpath(filename, LOCALE_DIR)
    out, err = call(['msgfmt', '-c', rfile], working_directory=LOCALE_DIR)
    if err != '':
        log.info('\n' + out)
        log.warn('\n' + err)
    assert not err


def tags_in_string(msg):
    """
    Return the set of tags in a message string.

    Tags includes HTML tags, data placeholders, etc.

    Skips tags that might change due to translations: HTML entities, <abbr>,
    and so on.

    """
    def is_linguistic_tag(tag):
        """Is this tag one that can change with the language?"""
        if tag.startswith("&"):
            return True
        if any(x in tag for x in ["<abbr>", "<abbr ", "</abbr>"]):
            return True
        return False

    __, tags = Converter().detag_string(msg)
    return set(t for t in tags if not is_linguistic_tag(t))


def astral(msg):
    """Does `msg` have characters outside the Basic Multilingual Plane?"""
    return any(ord(c) > 0xFFFF for c in msg)


def check_messages(filename, report_empty=False):
    """
    Checks messages in various ways:

    Translations must have the same slots as the English. Messages can't have astral
    characters in them.

    If report_empty is True, will also report empty translation strings.

    """
    # Don't check English files.
    if "/locale/en/" in filename:
        return

    # problems will be a list of tuples.  Each is a description, and a msgid,
    # and then zero or more translations.
    problems = []
    pomsgs = polib.pofile(filename)
    for msg in pomsgs:
        # Check for characters Javascript can't support.
        # https://code.djangoproject.com/ticket/21725
        if astral(msg.msgstr):
            problems.append(("Non-BMP char", msg.msgid, msg.msgstr))

        if msg.msgid_plural:
            # Plurals: two strings in, N strings out.
            source = msg.msgid + " | " + msg.msgid_plural
            translation = " | ".join(v for k, v in sorted(msg.msgstr_plural.items()))
            empty = any(not t.strip() for t in msg.msgstr_plural.values())
        else:
            # Singular: just one string in and one string out.
            source = msg.msgid
            translation = msg.msgstr
            empty = not msg.msgstr.strip()

        if empty:
            if report_empty:
                problems.append(("Empty translation", source))
        else:
            id_tags = tags_in_string(source)
            tx_tags = tags_in_string(translation)

            # Check if tags don't match
            if id_tags != tx_tags:
                id_has = u", ".join(u'"{}"'.format(t) for t in id_tags - tx_tags)
                tx_has = u", ".join(u'"{}"'.format(t) for t in tx_tags - id_tags)
                if id_has and tx_has:
                    diff = u"{} vs {}".format(id_has, tx_has)
                elif id_has:
                    diff = u"{} missing".format(id_has)
                else:
                    diff = u"{} added".format(tx_has)
                problems.append((
                    "Different tags in source and translation",
                    source,
                    translation,
                    diff
                ))

    if problems:
        problem_file = filename.replace(".po", ".prob")
        id_filler = textwrap.TextWrapper(width=79, initial_indent="  msgid: ", subsequent_indent=" " * 9)
        tx_filler = textwrap.TextWrapper(width=79, initial_indent="  -----> ", subsequent_indent=" " * 9)
        with codecs.open(problem_file, "w", encoding="utf8") as prob_file:
            for problem in problems:
                desc, msgid = problem[:2]
                prob_file.write(u"{}\n{}\n".format(desc, id_filler.fill(msgid)))
                for translation in problem[2:]:
                    prob_file.write(u"{}\n".format(tx_filler.fill(translation)))
                prob_file.write(u"\n")

        log.error(" {0} problems in {1}, details in .prob file".format(len(problems), filename))
    else:
        log.info(" No problems found in {0}".format(filename))


def parse_args(argv):
    """
    Parse command line arguments, returning a dict of
    valid options:

        {
            'empty': BOOLEAN,
            'verbose': BOOLEAN,
            'language': str
        }

    where 'language' is a language code, eg "fr"
    """
    parser = argparse.ArgumentParser(description="Automatically finds translation errors in all edx-platform *.po files, for all languages, unless one or more language(s) is specified to check.")

    parser.add_argument(
        '-l', '--language',
        type=str,
        nargs='*',
        help="Specify one or more specific language code(s) to check (eg 'ko_KR')."
    )

    parser.add_argument(
        '-e', '--empty',
        action='store_true',
        help="Includes empty translation strings in .prob files."
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Turns on info-level logging."
    )

    return vars(parser.parse_args(argv))


def main():
    """Main entry point for the tool."""

    args_dict = parse_args(sys.argv[1:])
    if args_dict['verbose']:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.WARNING)

    langs = args_dict['language']

    if langs is not None:
        # lang will be a list of language codes; test each language.
        for lang in langs:
            root = LOCALE_DIR / lang
            # Assert that a directory for this language code exists on the system
            if not os.path.isdir(root):
                log.error(" {0} is not a valid directory.\nSkipping language '{1}'".format(root, lang))
                continue
            # If we found the language code's directory, validate the files.
            validate_po_files(root, args_dict['empty'])

    else:
        # If lang is None, we walk all of the .po files under root, and test each one.
        root = LOCALE_DIR
        validate_po_files(root, args_dict['empty'])

if __name__ == '__main__':
    main()
