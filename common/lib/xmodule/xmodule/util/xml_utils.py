"""
Utility functions related to xml data formatting.
"""


def is_valid_xml_char(char):
    """
    Return only those characters which lie in legal XML characters range
    http://www.w3.org/TR/2008/REC-xml-20081126/#charsets

    Based on an answer by John Machin (http://stackoverflow.com/users/84270/john-machin) on StackOverflow
    http://stackoverflow.com/questions/8733233/filtering-out-certain-bytes-in-python
    """
    code_point = ord(char)
    # conditions ordered by presumed frequency
    return (
        0x20 <= code_point <= 0xD7FF or
        code_point in (0x9, 0xA, 0xD) or
        0xE000 <= code_point <= 0xFFFD or
        0x10000 <= code_point <= 0x10FFFF
    )


def filter_invalid_xml_chars(string_to_parse):
    """
    Filter characters outside the legal XML characters range
    """
    return filter(is_valid_xml_char, string_to_parse)
