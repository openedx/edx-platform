"""
Classes representing asset & asset thumbnail metadata.
"""

from datetime import datetime
import pytz
from contracts import contract, new_contract
from opaque_keys.edx.keys import CourseKey, AssetKey

new_contract('AssetKey', AssetKey)
new_contract('datetime', datetime)
new_contract('basestring', basestring)


class IncorrectAssetIdType(Exception):
    """
    Raised when the asset ID passed-in to create an AssetMetadata or
    AssetThumbnailMetadata is of the wrong type.
    """
    pass


class AssetMetadata(object):
    """
    Stores the metadata associated with a particular course asset. The asset metadata gets stored
    in the modulestore.
    """

    TOP_LEVEL_ATTRS = ['basename', 'internal_name', 'locked', 'contenttype', 'md5']
    EDIT_INFO_ATTRS = ['curr_version', 'prev_version', 'edited_by', 'edited_on']
    ALLOWED_ATTRS = TOP_LEVEL_ATTRS + EDIT_INFO_ATTRS

    # All AssetMetadata objects should have AssetLocators with this type.
    ASSET_TYPE = 'asset'

    @contract(asset_id='AssetKey', basename='basestring | None', internal_name='str | None', locked='bool | None', contenttype='basestring | None',
              md5='str | None', curr_version='str | None', prev_version='str | None', edited_by='int | None', edited_on='datetime | None')
    def __init__(self, asset_id,
                 basename=None, internal_name=None,
                 locked=None, contenttype=None, md5=None,
                 curr_version=None, prev_version=None,
                 edited_by=None, edited_on=None, field_decorator=None):
        """
        Construct a AssetMetadata object.

        Arguments:
            asset_id (AssetKey): Key identifying this particular asset.
            basename (str): Original path to file at asset upload time.
            internal_name (str): Name under which the file is stored internally.
            locked (bool): If True, only course participants can access the asset.
            contenttype (str): MIME type of the asset.
            curr_version (str): Current version of the asset.
            prev_version (str): Previous version of the asset.
            edited_by (str): Username of last user to upload this asset.
            edited_on (datetime): Datetime of last upload of this asset.
            field_decorator (function): used by strip_key to convert OpaqueKeys to the app's understanding
        """
        if asset_id.asset_type != self.ASSET_TYPE:
            raise IncorrectAssetIdType()
        self.asset_id = asset_id if field_decorator is None else field_decorator(asset_id)
        self.basename = basename  # Path w/o filename.
        self.internal_name = internal_name
        self.locked = locked
        self.contenttype = contenttype
        self.md5 = md5
        self.curr_version = curr_version
        self.prev_version = prev_version
        self.edited_by = edited_by
        self.edited_on = edited_on or datetime.now(pytz.utc)

    def __repr__(self):
        return """AssetMetadata{!r}""".format((
            self.asset_id,
            self.basename, self.internal_name,
            self.locked, self.contenttype, self.md5,
            self.curr_version, self.prev_version,
            self.edited_by, self.edited_on
        ))

    def update(self, attr_dict):
        """
        Set the attributes on the metadata. Ignore all those outside the known fields.

        Arguments:
            attr_dict: Prop, val dictionary of all attributes to set.
        """
        for attr, val in attr_dict.iteritems():
            if attr in self.ALLOWED_ATTRS:
                setattr(self, attr, val)

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
            'md5': self.md5,
            'edit_info': {
                'curr_version': self.curr_version,
                'prev_version': self.prev_version,
                'edited_by': self.edited_by,
                'edited_on': self.edited_on
            }
        }

    @contract(asset_doc='dict | None')
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
        self.md5 = asset_doc['md5']
        edit_info = asset_doc['edit_info']
        self.curr_version = edit_info['curr_version']
        self.prev_version = edit_info['prev_version']
        self.edited_by = edit_info['edited_by']
        self.edited_on = edit_info['edited_on']


class AssetThumbnailMetadata(object):
    """
    Stores the metadata associated with the thumbnail of a course asset.
    """

    # All AssetThumbnailMetadata objects should have AssetLocators with this type.
    ASSET_TYPE = 'thumbnail'

    @contract(asset_id='AssetKey', internal_name='str | unicode | None')
    def __init__(self, asset_id, internal_name=None, field_decorator=None):
        """
        Construct a AssetThumbnailMetadata object.

        Arguments:
            asset_id (AssetKey): Key identifying this particular asset.
            internal_name (str): Name under which the file is stored internally.
        """
        if asset_id.asset_type != self.ASSET_TYPE:
            raise IncorrectAssetIdType()
        self.asset_id = asset_id if field_decorator is None else field_decorator(asset_id)
        self.internal_name = internal_name

    def __repr__(self):
        return """AssetMetadata{!r}""".format((self.asset_id, self.internal_name))

    def to_mongo(self):
        """
        Converts metadata properties into a MongoDB-storable dict.
        """
        return {
            'filename': self.asset_id.path,
            'internal_name': self.internal_name
        }

    @contract(thumbnail_doc='dict | None')
    def from_mongo(self, thumbnail_doc):
        """
        Fill in all metadata fields from a MongoDB document.

        The asset_id prop is initialized upon construction only.
        """
        if thumbnail_doc is None:
            return
        self.internal_name = thumbnail_doc['internal_name']
