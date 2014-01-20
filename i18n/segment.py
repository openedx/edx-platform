#!/usr/bin/env python
"""
Segment a .po file to produce smaller files based on the locations of the
messages.
"""

import copy
import fnmatch
import logging
import sys

import polib

from i18n.config import CONFIGURATION

LOG = logging.getLogger(__name__)


def segment_pofiles(locale):
    """Segment all the pofiles for `locale`.

    Returns a set of filenames, all the segment files written.

    """
    files_written = set()
    for filename, segments in CONFIGURATION.segment.items():
        filename = CONFIGURATION.get_messages_dir(locale) / filename
        files_written.update(segment_pofile(filename, segments))
    return files_written


def segment_pofile(filename, segments):
    """Segment a .po file using patterns in `segments`.

    The .po file at `filename` is read, and the occurrence locations of its
    messages are examined.  `segments` is a dictionary: the keys are segment
    .po filenames, the values are lists of patterns::

        {
            'django-studio.po': [
                'cms/*',
                'some-other-studio-place/*',
            ],
            'django-weird.po': [
                '*/weird_*.*',
            ],
        }

    If all a message's occurrences match the patterns for a segment, then that
    message is written to the new segmented .po file.

    Any message that matches no segments, or more than one, is written back to
    the original file.

    Arguments:
        filename (path.path): a path object referring to the original .po file.
        segments (dict): specification of the segments to create.

    Returns:
        a set of path objects, all the segment files written.

    """
    reading_msg = "Reading {num} entries from {file}"
    writing_msg = "Writing {num} entries to {file}"

    source_po = polib.pofile(filename)
    LOG.info(reading_msg.format(file=filename, num=len(source_po)))

    # A new pofile just like the source, but with no messages. We'll put
    # anything not segmented into this file.
    remaining_po = copy.deepcopy(source_po)
    remaining_po[:] = []

    # Turn the segments dictionary into two structures: segment_patterns is a
    # list of (pattern, segmentfile) pairs.  segment_po_files is a dict mapping
    # segment file names to pofile objects of their contents.
    segment_po_files = {filename: remaining_po}
    segment_patterns = []
    for segmentfile, patterns in segments.items():
        segment_po_files[segmentfile] = copy.deepcopy(remaining_po)
        segment_patterns.extend((pat, segmentfile) for pat in patterns)

    # Examine each message in the source file. If all of its occurrences match
    # a pattern for the same segment, it goes in that segment.  Otherwise, it
    # goes in remaining.
    for msg in source_po:
        msg_segments = set()
        for occ_file, _ in msg.occurrences:
            for pat, segment_file in segment_patterns:
                if fnmatch.fnmatch(occ_file, pat):
                    msg_segments.add(segment_file)
                    break
            else:
                msg_segments.add(filename)

        if len(msg_segments) == 1:
            # This message belongs in this segment.
            segment_file = msg_segments.pop()
            segment_po_files[segment_file].append(msg)
        else:
            # Either it's in more than one segment, or none, so put it back in
            # the main file.
            remaining_po.append(msg)

    # Write out the results.
    files_written = set()
    for segment_file, pofile in segment_po_files.items():
        out_file = filename.dirname() / segment_file
        if len(pofile) == 0:
            LOG.error("No messages to write to {file}, did you run segment twice?".format(file=out_file))
        else:
            LOG.info(writing_msg.format(file=out_file, num=len(pofile)))
            pofile.save(out_file)
            files_written.add(out_file)

    LOG.info(writing_msg.format(file=filename, num=len(remaining_po)))
    remaining_po.save(filename)

    return files_written


def main(argv):
    """
    $ segment.py LOCALE [...]

    Segment the .po files in LOCALE(s) based on the segmenting rules in
    config.yaml.

    Note that segmenting is *not* idempotent: it modifies the input file, so
    be careful that you don't run it twice on the same file.

    """
    # This is used as a tool only to segment translation files when adding a
    # new segment.  In the regular workflow, the work is done by the extract
    # phase calling the functions above.

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    if len(argv) < 2:
        sys.exit("Need a locale to segment")
    for locale in argv[1:]:
        segment_pofiles(locale)


if __name__ == "__main__":
    main(sys.argv)
