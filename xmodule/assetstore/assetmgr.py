"""
Asset Manager

Interface allowing course asset saving/retrieving.
Handles:
  - saving asset in the BlobStore -and- saving asset metadata in course modulestore.
  - retrieving asset metadata from course modulestore -and- returning URL to asset -or- asset bytes.

Phase 1: Checks to see if an asset's metadata can be found in the course's modulestore.
    If not found, fails over to access the asset from the contentstore.
    At first, the asset metadata will never be found, since saving isn't implemented yet.
Note: Hotfix (PLAT-734) No asset calls find_asset_metadata, and directly accesses from contentstore.

"""

from xmodule.contentstore.django import contentstore


class AssetManager:
    """
    Manager for saving/loading course assets.
    """
    @staticmethod
    def find(asset_key, throw_on_not_found=True, as_stream=False):
        """
        Finds course asset in the deprecated contentstore.
        This method was previously searching for the course asset in the assetstore first, then in the deprecated
        contentstore. However, the asset was never found in the assetstore since an asset's metadata is
        not yet stored there.(removed calls to modulestore().find_asset_metadata(asset_key))
        The assetstore search was removed due to performance issues caused by each call unpickling the pickled and
        compressed course structure from the structure cache.
        """
        return contentstore().find(asset_key, throw_on_not_found, as_stream)
