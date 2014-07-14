"""
General utilities
"""
import urllib


def encode_key_for_mongo(fieldname):
    """
    Fieldnames in mongo cannot have periods nor dollar signs. So encode them.
    :param fieldname: an atomic field name. Note, don't pass structured paths as it will flatten them
    """
    for char in [".", "$"]:
        fieldname = fieldname.replace(char, '%{:02x}'.format(ord(char)))
    return fieldname


def decode_key_from_mongo(fieldname):
    """
    The inverse of encode_key_for_mongo
    :param fieldname: with period and dollar escaped
    """
    return urllib.unquote(fieldname)
