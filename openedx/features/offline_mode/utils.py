"""
Utility functions and classes for offline mode.
"""
import os
import logging
import shutil
from tempfile import mkdtemp

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.http.response import Http404

from zipfile import ZipFile

from .assets_management import block_storage_path, remove_old_files, is_modified
from .html_manipulator import HtmlManipulator

User = get_user_model()
log = logging.getLogger(__name__)


def generate_offline_content(xblock, html_data):
    """
    Generates archive with XBlock content for offline mode.

    Args:
        xblock (XBlock): The XBlock instance
        html_data (str): The rendered HTML representation of the XBlock
    """
    if not is_modified(xblock):
        return

    base_path = block_storage_path(xblock)
    remove_old_files(xblock)
    tmp_dir = mkdtemp()

    try:
        save_xblock_html(tmp_dir, xblock, html_data)
        create_zip_file(tmp_dir, base_path, f'{xblock.location.block_id}.zip')
    except Http404:
        log.error(
            f'Block {xblock.location.block_id} cannot be fetched from course'
            f' {xblock.location.course_key} during offline content generation.'
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def save_xblock_html(tmp_dir, xblock, html_data):
    """
    Saves the XBlock HTML content to a file.

    Generates the 'index.html' file with the HTML added to use it locally.
    Args:
        tmp_dir (str): The temporary directory path to save the xblock content
        xblock (XBlock): The XBlock instance
        html_data (str): The rendered HTML representation of the XBlock
    """
    html_manipulator = HtmlManipulator(xblock, html_data, tmp_dir)
    updated_html = html_manipulator.process_html()

    with open(os.path.join(tmp_dir, 'index.html'), 'w') as file:
        file.write(updated_html)


def create_zip_file(temp_dir, base_path, file_name):
    """
    Creates a zip file with the content of the base_path directory.

    Args:
        temp_dir (str): The temporary directory path where the content is stored
        base_path (str): The base path directory to save the zip file
        file_name (str): The name of the zip file
    """
    if not os.path.exists(default_storage.path(base_path)):
        os.makedirs(default_storage.path(base_path))

    with ZipFile(default_storage.path(base_path + file_name), 'w') as zip_file:
        zip_file.write(os.path.join(temp_dir, 'index.html'), 'index.html')
        add_files_to_zip_recursively(
            zip_file,
            current_base_path=os.path.join(temp_dir, 'assets'),
            current_path_in_zip='assets',
        )
    log.info(f'Offline content for {file_name} has been generated.')


def add_files_to_zip_recursively(zip_file, current_base_path, current_path_in_zip):
    """
    Recursively adds files to the zip file.

    Args:
        zip_file (ZipFile): The zip file object
        current_base_path (str): The current base path directory
        current_path_in_zip (str): The current path in the zip file
    """
    try:
        for resource_path in os.listdir(current_base_path):
            full_path = os.path.join(current_base_path, resource_path)
            full_path_in_zip = os.path.join(current_path_in_zip, resource_path)
            if os.path.isfile(full_path):
                zip_file.write(full_path, full_path_in_zip)
            else:
                add_files_to_zip_recursively(zip_file, full_path, full_path_in_zip)
    except OSError:
        log.error(f'Error while reading the directory: {current_base_path}')
        return
