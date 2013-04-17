import re, codecs
from operator import itemgetter

# Django stores externalized strings in .po and .mo files.
#  po files are human readable and contain metadata about the strings.
#  mo files are machine readable and optimized for runtime performance.

# See https://docs.djangoproject.com/en/1.3/topics/i18n/internationalization/
# See http://www.gnu.org/software/gettext/manual/html_node/PO-Files.html

# Usage:
#   >>> pofile = PoFile('/path/to/file')


class PoFile:

    # Django requires po files to be in UTF8 with no BOM (byte order marker)
    # see "Mind your charset" on this page:
    #     https://docs.djangoproject.com/en/1.3/topics/i18n/localization/

    ENCODING = 'utf_8'

    def __init__ (self, pathname):
        self.pathname = pathname
        self.parse()

    def parse (self):
        with codecs.open(self.pathname, 'r', self.ENCODING) as stream:
            text = stream.read()
        msgs = text.split('\n\n')
        self.msgs = [Msg.parse(m) for m in msgs]
        return msgs

    def write (self, out_pathname=None):
        if out_pathname == None:
            out_pathname = self.pathname
        with codecs.open(out_pathname, 'w', self.ENCODING) as stream:
            for msg in self.msgs:
                msg.write(stream)

class Msg:

    # A PoFile is parsed into a list of Msg objects, each of which corresponds
    # to an externalized string entry.

    # Each Msg object may contain multiple comment lines, capturing metadata
    
    # Each Msg has a property list (self.props) with a dict of key-values.
    # Each value is a list of strings
    kwords = ['msgid', 'msgstr', 'msgctxt', 'msgid_plural']

    # Line might begin with "msgid ..." or "msgid[2] ..."
    pattern = re.compile('^(\w+)(\[(\d+)\])?')
    
    @classmethod
    def parse (cls, string):
        '''
        String is a fragment of a pofile (.po) source file.
        This returns a Msg object created by parsing string.
        '''
        lines = string.strip().split('\n')
        msg = Msg()
        msg.comments = []
        msg.props = {}
        last_kword = None
        for line in lines:
            if line[0]=='#':
                msg.comments.append(line)
            elif line[0]=='"' and last_kword != None:
                msg.add_string(last_kword, line)
            else:
                match = cls.pattern.search(line)
                if match:
                    kword = match.group(1)
                    last_kword = kword
                    if kword in cls.kwords:
                        if match.group(3):
                            key = '%s[%s]' % (kword, match.group(3))
                            msg.add_string(key, line[len(key):])
                        else:
                            msg.add_string(kword, line[len(kword):])
        return msg
    
    def get_property (self, kword):
        '''returns value for kword. Typically returns a list of strings'''
        return self.props.get(kword, [])

    def set_property (self, kword, value):
        '''sets value for kword. Typically returns a list of strings'''
        self.props[kword] = value

    def add_string (self, kword, line):
        '''Append line to the list of values stored for the property kword'''
        props = self.props
        value = self.get_property(kword)
        value.append(self.cleanup_string(line))
        self.set_property(kword, value)

    def cleanup_string(self, string):
        string = string.strip()
        if len(string)>1 and string[0]=='"' and string[-1]=='"':
            return string[1:-1]
        else:
            return string

    def write (self, stream):
        '''Write a Msg to stream'''
        for comment in self.comments:
            stream.write(comment)
            stream.write('\n')
        for (key, values) in self.sort(self.props.items()):
            stream.write(key + ' ')
            for value in values:
                stream.write('"'+value+'"')
                stream.write('\n')
        stream.write('\n')

    # Preferred ordering of key output
    # Always print 'msgctxt' first, then 'msgid', etc.
    KEY_ORDER = ('msgctxt', 'msgid', 'msgid_plural', 'msgstr', 'msgstr[0]', 'msgstr[1]')

    def keyword_compare (self, k1, k2):
        for key in self.KEY_ORDER:
            if key == k1:
                return -1
            if key == k2:
                return 1
        return 0

    def sort (self, plist):
        '''sorts a propertylist to bring the high-priority keys to the beginning of the list'''
        return sorted(plist, key=itemgetter(0), cmp=self.keyword_compare)



# Testing
#
# >>> file  = 'mitx/conf/locale/en/LC_MESSAGES/django.po'
# >>> file1 = 'mitx/conf/locale/en/LC_MESSAGES/django1.po'
# >>> po = PoFile(file)
# >>> po.write(file1)
# $ diff file file1

