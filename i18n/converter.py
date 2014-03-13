import re
import itertools


class Converter(object):
    """Converter is an abstract class that transforms strings.
       It hides embedded tags (HTML or Python sequences) from transformation

       To implement Converter, provide implementation for inner_convert_string()

       Strategy:
         1. extract tags embedded in the string
           a. use the index of each extracted tag to re-insert it later
           b. replace tags in string with numbers (<0>, <1>, etc.)
           c. save extracted tags in a separate list
         2. convert string
         3. re-insert the extracted tags

    """

    # matches tags like these:
    #   HTML:   <B>, </B>, <BR/>, <textformat leading="10">
    #   Python: %(date)s, %(name)s
    tag_pattern = re.compile(
        r'''
        (<[^>]+>)           |       # <tag>
        ({[^}]+})           |       # {tag}
        (%\([\w]+\)\w)      |       # %(tag)s
        (&\w+;)             |       # &entity;
        (&\#\d+;)           |       # &#1234;
        (&\#x[0-9a-f]+;)            # &#xABCD;
        ''',
        re.IGNORECASE | re.VERBOSE
    )

    def convert(self, string):
        """Returns: a converted tagged string
           param: string (contains html tags)

           Don't replace characters inside tags
        """
        (string, tags) = self.detag_string(string)
        string = self.inner_convert_string(string)
        string = self.retag_string(string, tags)
        return string

    def detag_string(self, string):
        """Extracts tags from string.

           returns (string, list) where
           string: string has tags replaced by indices (<BR>... => <0>, <1>, <2>, etc.)
           list: list of the removed tags ('<BR>', '<I>', '</I>')
        """
        counter = itertools.count(0)
        count = lambda m: '<%s>' % counter.next()
        tags = self.tag_pattern.findall(string)
        tags = [''.join(tag) for tag in tags]
        (new, nfound) = self.tag_pattern.subn(count, string)
        if len(tags) != nfound:
            raise Exception('tags dont match:' + string)
        return (new, tags)

    def retag_string(self, string, tags):
        """substitutes each tag back into string, into occurrences of <0>, <1> etc"""
        for (i, tag) in enumerate(tags):
            p = '<%s>' % i
            string = re.sub(p, tag, string, 1)
        return string

    # ------------------------------
    # Customize this in subclasses of Converter

    def inner_convert_string(self, string):
        return string  # do nothing by default
