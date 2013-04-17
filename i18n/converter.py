import re, itertools

# Converter is an abstract class that transforms strings.
# It hides embedded tags (HTML or Python sequences) from transformation
#
# To implement Converter, provide implementation for inner_convert_string()


class Converter:

    # matches tags like these:
    #     HTML:   <B>, </B>, <BR/>, <textformat leading="10">
    #     Python: %(date)s, %(name)s
    #
    tag_pattern = re.compile(r'(<[-\w" .:?=/]*>)|({[^}]*})|(%\(.*\)\w)', re.I)


    def convert (self, string):
        if self.tag_pattern.search(string):
            result = self.convert_tagged_string(string)
        else:
            result = self.inner_convert_string(string)
        return result

    # convert_tagged_string(string):
    #    returns: a converted tagged string
    #    param: string (contains html tags)
    #
    #    Don't replace characters inside tags
    #
    # Strategy:
    #    1. extract tags embedded in the string
    #      a. use the index of each extracted tag to re-insert it later
    #      b. replace tags in string with numbers (<0>, <1>, etc.)
    #      c. save extracted tags in a separate list
    #    2. convert string
    #    3. re-insert the extracted tags
    #
    def convert_tagged_string (self, string):
        (string, tags) = self.detag_string(string)
        string = self.inner_convert_string(string)
        string = self.retag_string(string, tags)
        return string

    # extracts tags from string.
    #
    # returns (string, list) where
    #   string: string has tags replaced by indices (<BR>... => <0>, <1>, <2>, etc.)
    #   list: list of the removed tags ("<BR>", "<I>", "</I>")
    def detag_string (self, string):
        counter = itertools.count(0)
        count = lambda m: '<%s>' % counter.next()
        tags = self.tag_pattern.findall(string)
        tags = [''.join(tag) for tag in tags]
        (new, nfound) = self.tag_pattern.subn(count, string)
        if len(tags) != nfound:
            raise Exception('tags dont match:'+string)
        return (new, tags)

    # substitutes each tag back into string, into occurrences of <0>, <1> etc
    #
    def retag_string (self, string, tags):
        for (i, tag) in enumerate(tags):
            p = '<%s>' % i
            string = re.sub(p, tag, string, 1)
        return string


    # ------------------------------
    # Customize this in subclasses of Converter

    def inner_convert_string (self, string):
        return string  # do nothing by default

