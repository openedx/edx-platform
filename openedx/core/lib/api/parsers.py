from rest_framework import parsers


class MergePatchParser(parsers.JSONParser):
    """
    Custom parser to be used with the "merge patch" implementation (https://tools.ietf.org/html/rfc7396).
    """
    media_type = 'application/merge-patch+json'
