"""
API Client for Blockstore

TODO: This should all get ripped out.

TODO: This wrapper is extraneous now that Blockstore-as-a-service isn't supported.
      This whole directory tree should be removed by https://github.com/openedx/blockstore/issues/296.
"""
from blockstore.apps.api.data import (
    BundleFileData,
)
from blockstore.apps.api.exceptions import (
    CollectionNotFound,
    BundleNotFound,
    DraftNotFound,
    BundleVersionNotFound,
    BundleFileNotFound,
    BundleStorageError,
)
from blockstore.apps.api.methods import (
    # Collections:
    get_collection,
    create_collection,
    update_collection,
    delete_collection,
    # Bundles:
    get_bundles,
    get_bundle,
    create_bundle,
    update_bundle,
    delete_bundle,
    # Drafts:
    get_draft,
    get_or_create_bundle_draft,
    write_draft_file,
    set_draft_link,
    commit_draft,
    delete_draft,
    # Bundles or drafts:
    get_bundle_files,
    get_bundle_files_dict,
    get_bundle_file_metadata,
    get_bundle_file_data,
    get_bundle_version,
    get_bundle_version_files,
    # Links:
    get_bundle_links,
    get_bundle_version_links,
    # Misc:
    force_browser_url,
)
