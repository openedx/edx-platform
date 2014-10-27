"""
Asset Manager

Interface allowing course asset saving/retrieving.
Handles:
  - saving asset in the BlobStore -and- saving asset metadata in course modulestore.
  - retrieving asset metadata from course modulestore -and- returning URL to asset -or- asset bytes.

Phase 1: Checks to see if an asset's metadata can be found in the course's modulestore.
    If not found, fails over to access the asset from the contentstore.
    At first, the asset metadata will never be found, since saving isn't implemented yet.
"""

from contracts import contract, new_contract
from opaque_keys.edx.keys import AssetKey
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.assetstore import AssetMetadata, AssetThumbnailMetadata


new_contract('AssetKey', AssetKey)


class AssetException(Exception):
    """
    Base exception class for all exceptions related to assets.
    """
    pass


class AssetMetadataNotFound(AssetException):
    """
    Thrown when no asset metadata is present in the course modulestore for the particular asset requested.
    """
    pass


class UnknownAssetType(AssetException):
    """
    Thrown when the asset type is not recognized.
    """
    pass


class AssetMetadataFoundTemporary(AssetException):
    """
    TEMPORARY: Thrown if asset metadata is actually found in the course modulestore.
    """
    pass


class AssetManager(object):
    """
    Manager for saving/loading course assets.
    """
    @staticmethod
    @contract(asset_key='AssetKey', throw_on_not_found='bool', as_stream='bool')
    def find(asset_key, throw_on_not_found=True, as_stream=False):
        """
        Finds a course asset either in the assetstore -or- in the deprecated contentstore.
        """
        store = modulestore()
        content_md = None
        asset_type = asset_key.asset_type
        if asset_type == AssetThumbnailMetadata.ASSET_TYPE:
            content_md = store.find_asset_thumbnail_metadata(asset_key)
        elif asset_type == AssetMetadata.ASSET_TYPE:
            content_md = store.find_asset_metadata(asset_key)
        else:
            raise UnknownAssetType()

        # If found, raise an exception.
        if content_md:
            # For now, no asset metadata should be found in the modulestore.
            raise AssetMetadataFoundTemporary()
        else:
            # If not found, load the asset via the contentstore.
            return contentstore().find(asset_key, throw_on_not_found, as_stream)
