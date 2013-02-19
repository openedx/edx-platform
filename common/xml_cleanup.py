#!/usr/bin/env python

"""
Victor's xml cleanup script.  A big pile of useful hacks.  Do not use
without carefully reading the code and deciding that this is what you want.

In particular, the remove-meta option is only intended to be used after pulling out a policy
using the metadata_to_json management command.
"""

import os
import fnmatch
import re
import sys
from lxml import etree
from collections import defaultdict

INVALID_CHARS = re.compile(r"[^\w.-]")


def clean(value):
    """
    Return value, made into a form legal for locations
    """
    return re.sub('_+', '_', INVALID_CHARS.sub('_', value))


# category -> set of url_names for that category that we've already seen
used_names = defaultdict(set)


def clean_unique(category, name):
    cleaned = clean(name)
    if cleaned not in used_names[category]:
        used_names[category].add(cleaned)
        return cleaned
    x = 1
    while cleaned + str(x) in used_names[category]:
        x += 1

    # Found one!
    cleaned = cleaned + str(x)
    used_names[category].add(cleaned)
    return cleaned


def cleanup(filepath, remove_meta):
    # Keys that are exported to the policy file, and so
    # can be removed from the xml afterward
    to_remove = ('format', 'display_name',
                 'graceperiod', 'showanswer', 'rerandomize',
                 'start', 'due', 'graded', 'hide_from_toc',
                 'ispublic', 'xqa_key')

    try:
        print "Cleaning {0}".format(filepath)
        with open(filepath) as f:
            parser = etree.XMLParser(remove_comments=False)
            xml = etree.parse(filepath, parser=parser)
    except:
        print "Error parsing file {0}".format(filepath)
        return

    for node in xml.iter(tag=etree.Element):
        attrs = node.attrib
        if 'url_name' in attrs:
            used_names[node.tag].add(attrs['url_name'])
        if 'name' in attrs:
            # Replace name with an identical display_name, and a unique url_name
            name = attrs['name']
            attrs['display_name'] = name
            attrs['url_name'] = clean_unique(node.tag, name)
            del attrs['name']

        if 'url_name' in attrs and 'slug' in attrs:
            print "WARNING: {0} has both slug and url_name".format(node)

        if ('url_name' in attrs and 'filename' in attrs and
            len(attrs) == 2 and attrs['url_name'] == attrs['filename']):
            # This is a pointer tag in disguise.  Get rid of the filename.
            print 'turning {0}.{1} into a pointer tag'.format(node.tag, attrs['url_name'])
            del attrs['filename']

        if remove_meta:
            for attr in to_remove:
                if attr in attrs:
                    del attrs[attr]


    with open(filepath, "w") as f:
        f.write(etree.tostring(xml))


def find_replace(directory, filePattern, remove_meta):
    for path, dirs, files in os.walk(os.path.abspath(directory)):
        for filename in fnmatch.filter(files, filePattern):
            filepath = os.path.join(path, filename)
            cleanup(filepath, remove_meta)


def main(args):
    usage = "xml_cleanup [dir] [remove-meta]"
    n = len(args)
    if n < 1 or n > 2 or (n == 2 and args[1] != 'remove-meta'):
        print usage
        return

    remove_meta = False
    if n == 2:
        remove_meta = True

    find_replace(args[0], '*.xml', remove_meta)


if __name__ == '__main__':
    main(sys.argv[1:])
