#!/usr/bin/env python

"""
Victor's script to find tags with no url_name, and fix them.  A big pile of hacks.  Do not use
without carefully reading the code and deciding that this is what you want.
"""

import os, fnmatch, re, sys
from lxml import etree
from collections import defaultdict

# Only act on missing names for these tags
problem_tags = {'vertical': 'vert',
                'html': 'html_page'}

# Don't want to mess with random tags that aren't these.
module_tags = ('sequential', 'vertical', 'html', 'problem', 'customtag', 'video', 'videosequence', 'problemset')

# If none of these
specs = ('url_name', 'slug', 'name', 'display_name')

# category -> set of url_names for that category that we've already seen
used_names = defaultdict(set)

unnamed = defaultdict(int)     # category -> num of new url_names for that category

def cleanup(filepath, modify):
    """
    if modify is True, actually add names to nodes that don't have them.
    """

    def check_add_name(node, name):
        if name in used_names[node.tag]:
            print "ERROR: duplicate name {0} on node {1}".format(name, str(node))
        used_names[node.tag].add(name)

    modified = False
    try:
        print "Processing {0}".format(filepath)
        with open(filepath) as f:
            parser = etree.XMLParser(remove_comments=False)
            xml = etree.parse(filepath, parser=parser)
    except:
        print "Error parsing file {0}".format(filepath)
        return

    first = True
    for node in xml.iter(tag=etree.Element):
        # Don't care about the root tag--if this is the top of a file, it's not supposed to have a url name
        # (in most cases--there's supposed to be a pointer tag with it's url_name somewhere else)
        if first:
            first = False
            continue

        tag = node.tag
        if tag not in module_tags:
            continue

        attrs = node.attrib

        # NOTE: Only checking url_name uniqueness--may conflict with slugs,
        # names, etc.  Don't want to duplicate that logic here.  HACK HACK HACK.
        if 'url_name' in attrs:
            check_add_name(node, attrs['url_name'])

        if not any(spec in attrs for spec in specs):
            print "WARNING: {0} node has no name!".format(tag)
            if tag in problem_tags and modify:
                unnamed[tag] += 1
                # Assuming that this name hasn't been used before.
                new_name = problem_tags[tag] + '_' + str(unnamed[tag])
                while new_name in used_names[tag]:
                    unnamed[tag] += 1
                    new_name = problem_tags[tag] + '_' + str(unnamed[tag])

                attrs['url_name'] = new_name
                modified = True

    if modify and modified:
        print "WRITING new version"
        with open(filepath, "w") as f:
            f.write(etree.tostring(xml))


def find_replace(directory, filePattern, modify):
    for path, dirs, files in os.walk(os.path.abspath(directory)):
        for filename in fnmatch.filter(files, filePattern):
            filepath = os.path.join(path, filename)
            cleanup(filepath, modify)


def main(args):
    usage = "fix_tag_names [dir] [modify]"
    n = len(args)
    if n < 1 or n > 2 or (n == 2 and args[1] != 'modify'):
        print usage
        return
    modify = (n == 2 and args[1] == 'modify')

    find_replace(args[0], '*.xml', modify)


if __name__ == '__main__':
    main(sys.argv[1:])


