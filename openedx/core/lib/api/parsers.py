"""
Custom DRF request parsers.  These can be used by views to handle different
content types, as specified by `<Parser>.media_type`.

To use these in an APIView, set `<View>.parser_classes` to a list including the
desired parsers.  See http://www.django-rest-framework.org/api-guide/parsers/
for details.
"""

from rest_framework.exceptions import ParseError, UnsupportedMediaType
from rest_framework.parsers import FileUploadParser, JSONParser


class TypedFileUploadParser(FileUploadParser):
    """
    Handles upload of files, ensuring that the media type is supported, and
    that the uploaded filename matches the Content-type.

    Requirements:
        * The view must have an `upload_media_types` attribute which is a
          set (or other container) enumerating the mimetypes of the supported
          media formats

          Example:

              View.upload_media_types = {'audio/mp3', 'audio/ogg', 'audio/wav'}

        * Content-type must be set to a supported type (as
          defined in View.upload_media_types above).

          Example:

              Content-type: audio/ogg

        * Content-disposition must include a filename with a valid extension
          for the specified Content-type.

          Example:

              Content-disposition: attachment; filename="lecture-1.ogg"
    """

    media_type = '*/*'

    # Add more entries to this as needed.  All extensions should be lowercase.
    file_extensions = {
        'image/gif': {'.gif'},
        'image/jpeg': {'.jpeg', '.jpg'},
        'image/pjpeg': {'.jpeg', '.jpg'},
        'image/png': {'.png'},
        'image/svg': {'.svg'},
    }

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parse the request, returning a DataAndFiles object with the data dict
        left empty, and the body of the request placed in files['file'].
        """

        upload_media_types = getattr(parser_context['view'], 'upload_media_types', set())
        if media_type not in upload_media_types:
            raise UnsupportedMediaType(media_type)

        filename = self.get_filename(stream, media_type, parser_context)
        if media_type in self.file_extensions:
            fileparts = filename.rsplit('.', 1)
            if len(fileparts) < 2:
                ext = ''
            else:
                ext = '.{}'.format(fileparts[1])
            if ext.lower() not in self.file_extensions[media_type]:
                errmsg = (
                    u'File extension does not match requested Content-type. '
                    u'Filename: "{filename}", Content-type: "{contenttype}"'
                )
                raise ParseError(errmsg.format(filename=filename, contenttype=media_type))
        return super(TypedFileUploadParser, self).parse(stream, media_type, parser_context)


class MergePatchParser(JSONParser):
    """
    Custom parser to be used with the "merge patch" implementation (https://tools.ietf.org/html/rfc7396).
    """
    media_type = 'application/merge-patch+json'
