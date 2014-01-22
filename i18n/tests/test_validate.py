"""Tests that validate .po files."""

import codecs
import logging
import os
import sys
import textwrap

import polib

from i18n.config import LOCALE_DIR
from i18n.execute import call
from i18n.converter import Converter


def test_po_files(root=LOCALE_DIR):
    """
    This is a generator. It yields all of the .po files under root, and tests each one.
    """
    log = logging.getLogger(__name__)
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    for dirpath, __, filenames in os.walk(root):
        for name in filenames:
            __, ext = os.path.splitext(name)
            if ext.lower() == '.po':
                filename = os.path.join(dirpath, name)
                yield msgfmt_check_po_file, filename, log
                yield check_messages, filename


def msgfmt_check_po_file(filename, log):
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


def check_messages(filename):
    """
    Checks messages in various ways:

    Translations must have the same slots as the English.  The translation
    must not be empty. Messages can't have astral characters in them.

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
            translation = " | ".join(v for k,v in sorted(msg.msgstr_plural.items()))
            empty = any(not t.strip() for t in msg.msgstr_plural.values())
        else:
            # Singular: just one string in and one string out.
            source = msg.msgid
            translation = msg.msgstr
            empty = not msg.msgstr.strip()

        if empty:
            problems.append(("Empty translation", source))
        else:
            id_tags = tags_in_string(source)
            tx_tags = tags_in_string(translation)
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

    assert not problems, "Found %d problems in %s, details in .prob file" % (len(problems), filename)
