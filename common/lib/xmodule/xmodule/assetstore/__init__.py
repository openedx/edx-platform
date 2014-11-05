"""
Classes representing asset metadata.
"""

from datetime import datetime
import pytz
from contracts import contract, new_contract
from bisect import bisect_left, bisect_right
from opaque_keys.edx.keys import CourseKey, AssetKey

new_contract('AssetKey', AssetKey)
new_contract('datetime', datetime)
new_contract('basestring', basestring)


class AssetMetadata(object):
    """
    Stores the metadata associated with a particular course asset. The asset metadata gets stored
    in the modulestore.
    """

    TOP_LEVEL_ATTRS = ['basename', 'internal_name', 'locked', 'contenttype', 'thumbnail', 'fields']
    EDIT_INFO_ATTRS = ['curr_version', 'prev_version', 'edited_by', 'edited_on']
    ALLOWED_ATTRS = TOP_LEVEL_ATTRS + EDIT_INFO_ATTRS

    # Default type for AssetMetadata objects. A constant for convenience.
    ASSET_TYPE = 'asset'

    @contract(asset_id='AssetKey', basename='basestring|None', internal_name='basestring|None', locked='bool|None', contenttype='basestring|None',
              fields='dict | None', curr_version='basestring|None', prev_version='basestring|None', edited_by='int|None', edited_on='datetime|None')
    def __init__(self, asset_id,
                 basename=None, internal_name=None,
                 locked=None, contenttype=None, thumbnail=None, fields=None,
                 curr_version=None, prev_version=None,
                 edited_by=None, edited_on=None,
                 field_decorator=None,):
        """
        Construct a AssetMetadata object.

        Arguments:
            asset_id (AssetKey): Key identifying this particular asset.
            basename (str): Original path to file at asset upload time.
            internal_name (str): Name, url, or handle for the storage system to access the file.
            locked (bool): If True, only course participants can access the asset.
            contenttype (str): MIME type of the asset.
            thumbnail (str): the internal_name for the thumbnail if one exists
            fields (dict): fields to save w/ the metadata
            curr_version (str): Current version of the asset.
            prev_version (str): Previous version of the asset.
            edited_by (str): Username of last user to upload this asset.
            edited_on (datetime): Datetime of last upload of this asset.
            field_decorator (function): used by strip_key to convert OpaqueKeys to the app's understanding.
                Not saved.
        """
        self.asset_id = asset_id if field_decorator is None else field_decorator(asset_id)
        self.basename = basename  # Path w/o filename.
        self.internal_name = internal_name
        self.locked = locked
        self.contenttype = contenttype
        self.thumbnail = thumbnail
        self.curr_version = curr_version
        self.prev_version = prev_version
        self.edited_by = edited_by
        self.edited_on = edited_on or datetime.now(pytz.utc)
        self.fields = fields or {}

    def __repr__(self):
        return """AssetMetadata{!r}""".format((
            self.asset_id,
            self.basename, self.internal_name,
            self.locked, self.contenttype, self.fields,
            self.curr_version, self.prev_version,
            self.edited_by, self.edited_on
        ))

    def update(self, attr_dict):
        """
        Set the attributes on the metadata. Any which are not in ALLOWED_ATTRS get put into
        fields.

        Arguments:
            attr_dict: Prop, val dictionary of all attributes to set.
        """
        for attr, val in attr_dict.iteritems():
            if attr in self.ALLOWED_ATTRS:
                setattr(self, attr, val)
            else:
                self.fields[attr] = val

    def to_mongo(self):
        """
        Converts metadata properties into a MongoDB-storable dict.
        """
        return {
            'filename': self.asset_id.path,
            'basename': self.basename,
            'internal_name': self.internal_name,
            'locked': self.locked,
            'contenttype': self.contenttype,
            'thumbnail': self.thumbnail,
            'fields': self.fields,
            'curr_version': self.curr_version,
            'prev_version': self.prev_version,
            'edited_by': self.edited_by,
            'edited_on': self.edited_on
        }

    @contract(asset_doc='dict|None')
    def from_mongo(self, asset_doc):
        """
        Fill in all metadata fields from a MongoDB document.

        The asset_id prop is initialized upon construction only.
        """
        if asset_doc is None:
            return
        self.basename = asset_doc['basename']
        self.internal_name = asset_doc['internal_name']
        self.locked = asset_doc['locked']
        self.contenttype = asset_doc['contenttype']
        self.thumbnail = asset_doc['thumbnail']
        self.fields = asset_doc['fields']
        self.curr_version = asset_doc['curr_version']
        self.prev_version = asset_doc['prev_version']
        self.edited_by = asset_doc['edited_by']
        self.edited_on = asset_doc['edited_on']
