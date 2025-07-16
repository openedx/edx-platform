"""
This module contains utility functions for managing assets and files.
"""
import logging
import os
import requests

from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.storage import default_storage

from xmodule.assetstore.assetmgr import AssetManager
from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError
from xmodule.modulestore.exceptions import ItemNotFoundError

from .constants import MATHJAX_CDN_URL, MATHJAX_STATIC_PATH

log = logging.getLogger(__name__)


def get_static_file_path(relative_path):
    """
    Constructs the absolute path for a static file based on its relative path.
    """
    base_path = settings.STATIC_ROOT
    return os.path.join(base_path, relative_path)


def read_static_file(path):
    """
    Reads the contents of a static file in binary mode.
    """
    with open(path, 'rb') as file:
        return file.read()


def save_asset_file(temp_dir, xblock, path, filename):
    """
    Saves an asset file to the temporary directory.

    If the filename contains a '/', it reads the static file directly from the file system.
    Otherwise, it fetches the asset from the AssetManager.

    Args:
        temp_dir (str): The temporary directory where the assets are stored.
        xblock (XBlock): The XBlock instance
        path (str): The path where the asset is located.
        filename (str): The name of the file to be saved.
    """
    try:
        if filename.startswith('assets/'):
            asset_filename = filename.split('/')[-1]
            asset_key = StaticContent.get_asset_key_from_path(xblock.location.course_key, asset_filename)
            content = AssetManager.find(asset_key).data
            file_path = os.path.join(temp_dir, filename)
        else:
            static_path = get_static_file_path(filename)
            content = read_static_file(static_path)
            file_path = os.path.join(temp_dir, 'assets', filename)
    except (FileNotFoundError, ItemNotFoundError, NotFoundError):
        log.warning(f"Asset not found: {filename}, during offline content generation.")

    else:
        create_subdirectories_for_asset(file_path)
        with open(file_path, 'wb') as file:
            file.write(content)


def create_subdirectories_for_asset(file_path):
    """
    Creates the subdirectories for the asset file path if they do not exist.
    """
    out_dir_name = '/'
    for dir_name in file_path.split('/')[:-1]:
        out_dir_name = os.path.join(out_dir_name, dir_name)
        if out_dir_name and not os.path.exists(out_dir_name):
            os.mkdir(out_dir_name)


def clean_outdated_xblock_files(xblock):
    """
    Removes the old zip file with Offline Content from media storage.

    Args:
        (XBlock): The XBlock instance
    """
    try:
        base_path = block_storage_path(xblock)
        offline_zip_path = os.path.join(base_path, f'{xblock.location.block_id}.zip')

        if default_storage.exists(offline_zip_path):
            default_storage.delete(offline_zip_path)
            log.info(f"Successfully deleted the file: {offline_zip_path}")

    except ClientError as e:
        log.error(f"Error occurred while deleting the files or directory: {e}")


def get_offline_block_content_path(xblock=None, usage_key=None):
    """
    Checks whether 'offline_content.zip' file is present in the specified base path directory.

    Args:
        xblock (XBlock): The XBlock instance
        usage_key (UsageKey): The UsageKey of the XBlock
    Returns:
        bool: True if the file is present, False otherwise
    """
    usage_key = usage_key or getattr(xblock, 'location', None)
    base_path = block_storage_path(usage_key=usage_key)
    offline_zip_path = os.path.join(base_path, f'{usage_key.block_id}.zip')
    return offline_zip_path if default_storage.exists(offline_zip_path) else None


def block_storage_path(xblock=None, usage_key=None):
    """
    Generates the base storage path for the given XBlock.

    The path is constructed based on the XBlock's location, which includes the organization,
    course, block type, and block ID.

    Args:
        xblock (XBlock): The XBlock instance for which to generate the storage path.
        usage_key (UsageKey): The UsageKey of the XBlock.
    Returns:
        str: The constructed base storage path.
    """
    loc = usage_key or getattr(xblock, 'location', None)
    return f'offline_content/{str(loc.course_key)}/' if loc else ''


def is_modified(xblock):
    """
    Check if the xblock has been modified since the last time the offline content was generated.

    Args:
        xblock (XBlock): The XBlock instance to check.
    """
    file_path = os.path.join(block_storage_path(xblock), f'{xblock.location.block_id}.zip')

    try:
        last_modified = default_storage.get_modified_time(file_path)
    except (OSError, ClientError):
        return True

    return xblock.published_on > last_modified


def save_mathjax_to_xblock_assets(temp_dir):
    """
    Saves MathJax to the local static directory.

    If MathJax is not already saved, it fetches MathJax from
    the CDN and saves it to the local static directory.
    """
    file_path = os.path.join(temp_dir, MATHJAX_STATIC_PATH)
    if not os.path.exists(file_path):
        response = requests.get(MATHJAX_CDN_URL)
        with open(file_path, 'wb') as file:
            file.write(response.content)

        log.info(f"Successfully saved MathJax to {file_path}")


def save_external_file(temp_dir, link, filename):
    """
    Save external file to the local directory.
    """
    file_path = os.path.join(temp_dir, filename)
    try:
        response = requests.get(link)
    except requests.exceptions.RequestException as e:
        log.error(f"Failed to download {link}: {e}")
    else:
        create_subdirectories_for_asset(file_path)
        with open(file_path, 'wb') as file:
            file.write(response.content)
