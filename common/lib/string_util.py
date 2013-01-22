import itertools

def split_by_comma_and_whitespace(s):
    """
    Split a string both by on commas and whitespice.
    """
    # Note: split() with no args removes empty strings from output
    lists = [x.split() for x in s.split(',')]
    # return all of them
    return itertools.chain(*lists)

