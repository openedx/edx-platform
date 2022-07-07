# Xlib.rdb -- X resource database implementation
#
#    Copyright (C) 2000 Peter Liljenberg <petli@ctrl-c.liu.se>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


# See end of file for an explanation of the algorithm and
# data structures used.


# Standard modules
import functools
import re
import sys

# Xlib modules
from Xlib.support import lock

# Set up a few regexpes for parsing string representation of resources

comment_re = re.compile(r'^\s*!')
resource_spec_re = re.compile(r'^\s*([-_a-zA-Z0-9?.*]+)\s*:\s*(.*)$')
value_escape_re = re.compile('\\\\([ \tn\\\\]|[0-7]{3,3})')
resource_parts_re = re.compile(r'([.*]+)')

# Constants used for determining which match is best

NAME_MATCH = 0
CLASS_MATCH = 2
WILD_MATCH = 4
MATCH_SKIP = 6

# Option error class
class OptionError(Exception):
    pass


class ResourceDB:
    def __init__(self, file = None, string = None, resources = None):
        self.db = {}
        self.lock = lock.allocate_lock()

        if file is not None:
            self.insert_file(file)
        if string is not None:
            self.insert_string(string)
        if resources is not None:
            self.insert_resources(resources)

    def insert_file(self, file):
        """insert_file(file)

        Load resources entries from FILE, and insert them into the
        database.  FILE can be a filename (a string)or a file object.

        """

        if type(file) is str:
            file = open(file, 'r')

        self.insert_string(file.read())


    def insert_string(self, data):
        """insert_string(data)

        Insert the resources entries in the string DATA into the
        database.

        """

        # First split string into lines
        lines = data.split('\n')

        while lines:
            line = lines[0]
            del lines[0]

            # Skip empty line
            if not line:
                continue

            # Skip comments
            if comment_re.match(line):
                continue

            # Handle continued lines
            while line[-1] == '\\':
                if lines:
                    line = line[:-1] + lines[0]
                    del lines[0]
                else:
                    line = line[:-1]
                    break

            # Split line into resource and value
            m = resource_spec_re.match(line)

            # Bad line, just ignore it silently
            if not m:
                continue

            res, value = m.group(1, 2)

            # Convert all escape sequences in value
            splits = value_escape_re.split(value)

            for i in range(1, len(splits), 2):
                s = splits[i]
                if len(s) == 3:
                    splits[i] = chr(int(s, 8))
                elif s == 'n':
                    splits[i] = '\n'

            # strip the last value part to get rid of any
            # unescaped blanks
            splits[-1] = splits[-1].rstrip()

            value = ''.join(splits)

            self.insert(res, value)


    def insert_resources(self, resources):
        """insert_resources(resources)

        Insert all resources entries in the list RESOURCES into the
        database.  Each element in RESOURCES should be a tuple:

          (resource, value)

        Where RESOURCE is a string and VALUE can be any Python value.

        """

        for res, value in resources:
            self.insert(res, value)

    def insert(self, resource, value):
        """insert(resource, value)

        Insert a resource entry into the database.  RESOURCE is a
        string and VALUE can be any Python value.

        """

        # Split res into components and bindings
        parts = resource_parts_re.split(resource)

        # If the last part is empty, this is an invalid resource
        # which we simply ignore
        if parts[-1] == '':
            return

        self.lock.acquire()

        db = self.db
        for i in range(1, len(parts), 2):

            # Create a new mapping/value group
            if parts[i - 1] not in db:
                db[parts[i - 1]] = ({}, {})

            # Use second mapping if a loose binding, first otherwise
            if '*' in parts[i]:
                db = db[parts[i - 1]][1]
            else:
                db = db[parts[i - 1]][0]

        # Insert value into the derived db
        if parts[-1] in db:
            db[parts[-1]] = db[parts[-1]][:2] + (value, )
        else:
            db[parts[-1]] = ({}, {}, value)

        self.lock.release()

    def __getitem__(self, nc):
        """db[name, class]

        Return the value matching the resource identified by NAME and
        CLASS.  If no match is found, KeyError is raised.
        """
        name, cls = nc

        # Split name and class into their parts

        namep = name.split('.')
        clsp = cls.split('.')

        # It is an error for name and class to have different number
        # of parts

        if len(namep) != len(clsp):
            raise ValueError('Different number of parts in resource name/class: %s/%s' % (name, cls))

        complen = len(namep)
        matches = []

        # Lock database and wrap the lookup code in a try-finally
        # block to make sure that it is unlocked.

        self.lock.acquire()
        try:

            # Precedence order: name -> class -> ?

            if namep[0] in self.db:
                bin_insert(matches, _Match((NAME_MATCH, ), self.db[namep[0]]))

            if clsp[0] in self.db:
                bin_insert(matches, _Match((CLASS_MATCH, ), self.db[clsp[0]]))

            if '?' in self.db:
                bin_insert(matches, _Match((WILD_MATCH, ), self.db['?']))


            # Special case for the unlikely event that the resource
            # only has one component
            if complen == 1 and matches:
                x = matches[0]
                if x.final(complen):
                    return x.value()
                else:
                    raise KeyError((name, cls))


            # Special case for resources which begins with a loose
            # binding, e.g. '*foo.bar'
            if '' in self.db:
                bin_insert(matches, _Match((), self.db[''][1]))


            # Now iterate over all components until we find the best match.

            # For each component, we choose the best partial match among
            # the mappings by applying these rules in order:

            # Rule 1: If the current group contains a match for the
            # name, class or '?', we drop all previously found loose
            # binding mappings.

            # Rule 2: A matching name has precedence over a matching
            # class, which in turn has precedence over '?'.

            # Rule 3: Tight bindings have precedence over loose
            # bindings.

            while matches:

                # Work on the first element == the best current match

                x = matches[0]
                del matches[0]

                # print 'path:  ', x.path
                # if x.skip:
                #         print 'skip:  ', x.db
                # else:
                #         print 'group: ', x.group
                # print

                i = x.match_length()

                for part, score in ((namep[i], NAME_MATCH),
                                    (clsp[i], CLASS_MATCH),
                                    ('?', WILD_MATCH)):

                    # Attempt to find a match in x
                    match = x.match(part, score)
                    if match:
                        # Hey, we actually found a value!
                        if match.final(complen):
                            return match.value()

                        # Else just insert the new match
                        else:
                            bin_insert(matches, match)

                    # Generate a new loose match
                    match = x.skip_match(complen)
                    if match:
                        bin_insert(matches, match)

            # Oh well, nothing matched
            raise KeyError((name, cls))

        finally:
            self.lock.release()

    def get(self, res, cls, default = None):
        """get(name, class [, default])

        Return the value matching the resource identified by NAME and
        CLASS.  If no match is found, DEFAULT is returned, or None if
        DEFAULT isn't specified.

        """

        try:
            return self[(res, cls)]
        except KeyError:
            return default

    def update(self, db):
        """update(db)

        Update this database with all resources entries in the resource
        database DB.

        """

        self.lock.acquire()
        update_db(self.db, db.db)
        self.lock.release()

    def output(self):
        """output()

        Return the resource database in text representation.
        """

        self.lock.acquire()
        text = output_db('', self.db)
        self.lock.release()
        return text

    def getopt(self, name, argv, opts):
        """getopt(name, argv, opts)

        Parse X command line options, inserting the recognised options
        into the resource database.

        NAME is the application name, and will be prepended to all
        specifiers.  ARGV is the list of command line arguments,
        typically sys.argv[1:].

        OPTS is a mapping of options to resource specifiers.  The key is
        the option flag (with leading -), and the value is an instance of
        some Option subclass:

        NoArg(specifier, value): set resource to value.
        IsArg(specifier):        set resource to option itself
        SepArg(specifier):       value is next argument
        ResArg:                  resource and value in next argument
        SkipArg:                 ignore this option and next argument
        SkipLine:                ignore rest of arguments
        SkipNArgs(count):        ignore this option and count arguments

        The remaining, non-option, oparguments is returned.

        rdb.OptionError is raised if there is an error in the argument list.
        """

        while argv and argv[0] and argv[0][0] == '-':
            try:
                argv = opts[argv[0]].parse(name, self, argv)
            except KeyError:
                raise OptionError('unknown option: %s' % argv[0])
            except IndexError:
                raise OptionError('missing argument to option: %s' % argv[0])

        return argv


@functools.total_ordering
class _Match:
    def __init__(self, path, dbs):
        self.path = path

        if type(dbs) is tuple:
            self.skip = 0
            self.group = dbs

        else:
            self.skip = 1
            self.db = dbs

    def __eq__(self, other):
        return self.path == other.path

    def __lt__(self, other):
        return self.path < other.path

    def match_length(self):
        return len(self.path)

    def match(self, part, score):
        if self.skip:
            if part in self.db:
                return _Match(self.path + (score, ), self.db[part])
            else:
                return None
        else:
            if part in self.group[0]:
                return _Match(self.path + (score, ), self.group[0][part])
            elif part in self.group[1]:
                return _Match(self.path + (score + 1, ), self.group[1][part])
            else:
                return None

    def skip_match(self, complen):
        # Can't make another skip if we have run out of components
        if len(self.path) + 1 >= complen:
            return None

        # If this already is a skip match, clone a new one
        if self.skip:
            if self.db:
                return _Match(self.path + (MATCH_SKIP, ), self.db)
            else:
                return None

        # Only generate a skip match if the loose binding mapping
        # is non-empty
        elif self.group[1]:
            return _Match(self.path + (MATCH_SKIP, ), self.group[1])

        # This is a dead end match
        else:
            return None

    def final(self, complen):
        if not self.skip and len(self.path) == complen and len(self.group) > 2:
            return 1
        else:
            return 0

    def value(self):
        return self.group[2]


#
# Helper function for ResourceDB.__getitem__()
#

def bin_insert(list, element):
    """bin_insert(list, element)

    Insert ELEMENT into LIST.  LIST must be sorted, and ELEMENT will
    be inserted to that LIST remains sorted.  If LIST already contains
    ELEMENT, it will not be duplicated.

    """

    if not list:
        list.append(element)
        return

    lower = 0
    upper = len(list) - 1

    while lower <= upper:
        center = (lower + upper) // 2
        if element < list[center]:
            upper = center - 1
        elif element > list[center]:
            lower = center + 1
        elif element == list[center]:
            return

    if element < list[upper]:
        list.insert(upper, element)
    elif element > list[upper]:
        list.insert(upper + 1, element)


#
# Helper functions for ResourceDB.update()
#

def update_db(dest, src):
    for comp, group in src.items():

        # DEST already contains this component, update it
        if comp in dest:

            # Update tight and loose binding databases
            update_db(dest[comp][0], group[0])
            update_db(dest[comp][1], group[1])

            # If a value has been set in SRC, update
            # value in DEST

            if len(group) > 2:
                dest[comp] = dest[comp][:2] + group[2:]

        # COMP not in src, make a deep copy
        else:
            dest[comp] = copy_group(group)

def copy_group(group):
    return (copy_db(group[0]), copy_db(group[1])) + group[2:]

def copy_db(db):
    newdb = {}
    for comp, group in db.items():
        newdb[comp] = copy_group(group)

    return newdb


#
# Helper functions for output
#

def output_db(prefix, db):
    res = ''
    for comp, group in db.items():

        # There's a value for this component
        if len(group) > 2:
            res = res + '%s%s: %s\n' % (prefix, comp, output_escape(group[2]))

        # Output tight and loose bindings
        res = res + output_db(prefix + comp + '.', group[0])
        res = res + output_db(prefix + comp + '*', group[1])

    return res

def output_escape(value):
    value = str(value)
    if not value:
        return value

    for char, esc in (('\\', '\\\\'),
                      ('\000', '\\000'),
                      ('\n', '\\n')):

        value = value.replace(char, esc)

    # If first or last character is space or tab, escape them.
    if value[0] in ' \t':
        value = '\\' + value
    if value[-1] in ' \t' and value[-2:-1] != '\\':
        value = value[:-1] + '\\' + value[-1]

    return value


#
# Option type definitions
#

class Option:
    def __init__(self):
        pass

    def parse(self, name, db, args):
        pass

class NoArg(Option):
    """Value is provided to constructor."""
    def __init__(self, specifier, value):
        self.specifier = specifier
        self.value = value

    def parse(self, name, db, args):
        db.insert(name + self.specifier, self.value)
        return args[1:]

class IsArg(Option):
    """Value is the option string itself."""
    def __init__(self, specifier):
        self.specifier = specifier

    def parse(self, name, db, args):
        db.insert(name + self.specifier, args[0])
        return args[1:]

class SepArg(Option):
    """Value is the next argument."""
    def __init__(self, specifier):
        self.specifier = specifier

    def parse(self, name, db, args):
        db.insert(name + self.specifier, args[1])
        return args[2:]

class ResArgClass(Option):
    """Resource and value in the next argument."""
    def parse(self, name, db, args):
        db.insert_string(args[1])
        return args[2:]

ResArg = ResArgClass()

class SkipArgClass(Option):
    """Ignore this option and next argument."""
    def parse(self, name, db, args):
        return args[2:]

SkipArg = SkipArgClass()

class SkipLineClass(Option):
    """Ignore rest of the arguments."""
    def parse(self, name, db, args):
        return []

SkipLine = SkipLineClass()

class SkipNArgs(Option):
    """Ignore this option and the next COUNT arguments."""
    def __init__(self, count):
        self.count = count

    def parse(self, name, db, args):
        return args[1 + self.count:]



def get_display_opts(options, argv = sys.argv):
    """display, name, db, args = get_display_opts(options, [argv])

    Parse X OPTIONS from ARGV (or sys.argv if not provided).

    Connect to the display specified by a *.display resource if one is
    set, or to the default X display otherwise.  Extract the
    RESOURCE_MANAGER property and insert all resources from ARGV.

    The four return values are:
      DISPLAY -- the display object
      NAME    -- the application name (the filname of ARGV[0])
      DB      -- the created resource database
      ARGS    -- any remaining arguments
    """

    from Xlib import display, Xatom
    import os

    name = os.path.splitext(os.path.basename(argv[0]))[0]

    optdb = ResourceDB()
    leftargv = optdb.getopt(name, argv[1:], options)

    dname = optdb.get(name + '.display', name + '.Display', None)
    d = display.Display(dname)

    rdbstring = d.screen(0).root.get_full_property(Xatom.RESOURCE_MANAGER,
                                                   Xatom.STRING)
    if rdbstring:
        data = rdbstring.value
    else:
        data = None

    db = ResourceDB(string = data)
    db.update(optdb)

    return d, name, db, leftargv


# Common X options
stdopts = {'-bg': SepArg('*background'),
           '-background': SepArg('*background'),
           '-fg': SepArg('*foreground'),
           '-foreground': SepArg('*foreground'),
           '-fn': SepArg('*font'),
           '-font': SepArg('*font'),
           '-name': SepArg('.name'),
           '-title': SepArg('.title'),
           '-synchronous': NoArg('*synchronous', 'on'),
           '-xrm': ResArg,
           '-display': SepArg('.display'),
           '-d': SepArg('.display'),
           }


# Notes on the implementation:

# Resource names are split into their components, and each component
# is stored in a mapping.  The value for a component is a tuple of two
# or three elements:

#   (tightmapping, loosemapping [, value])

# tightmapping contains the next components which are connected with a
# tight binding (.).  loosemapping contains the ones connected with
# loose binding (*).  If value is present, then this component is the
# last component for some resource which that value.

# The top level components are stored in the mapping r.db, where r is
# the resource object.

# Example:  Inserting "foo.bar*gazonk: yep" into an otherwise empty
# resource database would give the folliwing structure:

# { 'foo': ( { 'bar': ( { },
#                       { 'gazonk': ( { },
#                                     { },
#                                     'yep')
#                         }
#                       )
#              },
#            {})
#   }
