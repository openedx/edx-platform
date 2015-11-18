"""
Utilities for dealing with JSON.
"""
import simplejson


from xmodule.modulestore import EdxJSONEncoder


class EscapedEdxJSONEncoder(EdxJSONEncoder):
    """
    Class for encoding edx JSON which will be printed inline into HTML
    templates.
    """
    def encode(self, obj):
        """
        Encodes JSON that is safe to be embedded in HTML.
        """
        return simplejson.dumps(
            simplejson.loads(super(EscapedEdxJSONEncoder, self).encode(obj)),
            cls=simplejson.JSONEncoderForHTML
        )
