"""
Helpers required to adapt to differing APIs
"""
import logging
import re
from contextlib import contextmanager

from fs.memoryfs import MemoryFS
from fs.wrapfs import WrapFS
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import AssetKey, CourseKey
from xmodule.assetstore.assetmgr import AssetManager
from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError
from xmodule.modulestore.django import modulestore as store
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.xml_block import XmlMixin

from common.djangoapps.static_replace import replace_static_urls

log = logging.getLogger(__name__)


def get_block(usage_key):
    """
    Return an XBlock from modulestore.
    """
    return store().get_item(usage_key)


def get_asset_content_from_path(course_key, asset_path):
    """
    Locate the given asset content, load it into memory, and return it.
    Returns None if the asset is not found.
    """
    try:
        asset_key = StaticContent.get_asset_key_from_path(course_key, asset_path)
        return AssetManager.find(asset_key)
    except (ItemNotFoundError, NotFoundError):
        return None


def rewrite_absolute_static_urls(text, course_id):
    """
    Convert absolute URLs like
        https://studio-site.opencraft.hosting/asset-v1:LabXchange+101+2019+type@asset+block@SCI_1.2_Image_.png
    to the proper
        /static/SCI_1.2_Image_.png
    format for consistency and portability.
    """
    assert isinstance(course_id, CourseKey)
    asset_full_url_re = r'https?://[^/]+/(?P<maybe_asset_key>[^\s\'"&]+)'

    def check_asset_key(match_obj):
        """
        If this URL's path part is an AssetKey from the same course, rewrite it.
        """
        try:
            asset_key = AssetKey.from_string(match_obj.group('maybe_asset_key'))
        except InvalidKeyError:
            return match_obj.group(0)  # Not an asset key; do not rewrite
        if asset_key.course_key == course_id:
            return '/static/' + asset_key.path  # Rewrite this to portable form
        else:
            return match_obj.group(0)  # From a different course; do not rewrite

    return re.sub(asset_full_url_re, check_asset_key, text)


def collect_assets_from_text(text, course_id, include_content=False):
    """
    Yield dicts of asset content and path from static asset paths found in the given text.
    Make sure to have replaced the URLs with rewrite_absolute_static_urls first.
    If include_content is True, the result will include a contentstore
    StaticContent file object which wraps the actual binary content of the file.
    """
    # Replace static urls like '/static/foo.png'
    static_paths = []
    # Drag-and-drop-v2 has
    #     &quot;/static/blah.png&quot;
    # which must be changed to "/static/blah.png" for replace_static_urls to work:
    text2 = text.replace("&quot;", '"')
    replace_static_urls(text=text2, course_id=course_id, static_paths_out=static_paths)
    for (path, uri) in static_paths:
        if path.startswith('/static/'):
            path = path[8:]
        info = {
            'path': path,
            'url': '/' + str(StaticContent.compute_location(course_id, path)),
        }
        if include_content:
            content = get_asset_content_from_path(course_id, path)
            if content is None:
                log.error("Static asset not found: (%s, %s)", path, uri)
            else:
                info['content'] = content
        yield info


@contextmanager
def override_export_fs(block):
    """
    Hack that makes some legacy XBlocks which inherit `XmlMixin.add_xml_to_node`
    instead of the usual `XmlSerialization.add_xml_to_node` serializable to a string.
    This is needed for the OLX export API.

    Originally, `add_xml_to_node` was `XModuleDescriptor`'s method and was migrated to `XmlMixin`
    as part of the content core platform refactoring. It differs from `XmlSerialization.add_xml_to_node`
    in that it relies on `XmlMixin.export_to_file` (or `CustomTagBlock.export_to_file`) method to control
    whether a block has to be exported as two files (one .olx pointing to one .xml) file, or a single XML node.

    For the legacy blocks (`AnnotatableBlock` for instance) `export_to_file` returns `True` by default.
    The only exception is `CustomTagBlock`, for which this method was originally developed, as customtags don't
    have to be exported as separate files.

    This method temporarily replaces a block's runtime's `export_fs` system with an in-memory filesystem.
    Also, it abuses the `XmlMixin.export_to_file` API to prevent the XBlock export code from exporting
    each block as two files (one .olx pointing to one .xml file).

    Although `XModuleDescriptor` has been removed a long time ago, we have to keep this hack untill the legacy
    `add_xml_to_node` implementation is removed in favor of `XmlSerialization.add_xml_to_node`, which itself
    is a hard task involving refactoring of `CourseExportManager`.
    """
    fs = WrapFS(MemoryFS())
    fs.makedir('course')
    fs.makedir('course/static')  # Video XBlock requires this directory to exists, to put srt files etc.

    old_export_fs = block.runtime.export_fs
    block.runtime.export_fs = fs
    if hasattr(block, 'export_to_file'):
        old_export_to_file = block.export_to_file
        block.export_to_file = lambda: False
    old_global_export_to_file = XmlMixin.export_to_file
    XmlMixin.export_to_file = lambda _: False  # So this applies to child blocks that get loaded during export
    yield fs
    block.runtime.export_fs = old_export_fs
    if hasattr(block, 'export_to_file'):
        block.export_to_file = old_export_to_file
    XmlMixin.export_to_file = old_global_export_to_file
