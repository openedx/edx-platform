"""
Utility functions and classes for offline mode.
"""
import os
import logging
import shutil
from tempfile import mkdtemp
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.http.response import Http404
from openedx.core.storage import get_storage
from zipfile import ZipFile

from .assets_management import block_storage_path, clean_outdated_xblock_files
from .html_manipulator import HtmlManipulator
from .renderer import XBlockRenderer

User = get_user_model()
log = logging.getLogger(__name__)


class OfflineContentGenerator:
    """
    Creates zip file with Offline Content in the media storage.
    """

    def __init__(self, xblock, html_data=None, storage_class=None, storage_kwargs=None):
        """
        Creates `SaveOfflineContentToStorage` object.
        Args:
            xblock (XBlock): The XBlock instance
            html_data (str): The rendered HTML representation of the XBlock
            storage_class: Used media storage class.
            storage_kwargs (dict): Additional storage attributes.
        """
        if storage_kwargs is None:
            storage_kwargs = {}
        self.xblock = xblock
        self.html_data = html_data or self.render_block_html_data()
        self.storage = get_storage(storage_class, **storage_kwargs)

    def render_block_html_data(self):
        """
        Renders the XBlock HTML content from the LMS.
        """
        try:
            return XBlockRenderer(str(self.xblock.location)).render_xblock_from_lms()
        except Http404 as e:
            log.error(
                f'Block {str(self.xblock.location)} cannot be fetched from course'
                f' {self.xblock.location.course_key} during offline content generation.'
            )
            raise e

    def generate_offline_content(self):
        """
        Generates archive with XBlock content for offline mode.
        """
        base_path = block_storage_path(self.xblock)
        clean_outdated_xblock_files(self.xblock)
        tmp_dir = mkdtemp()
        try:
            self.save_xblock_html(tmp_dir)
            self.create_zip_file(tmp_dir, base_path, f'{self.xblock.location.block_id}.zip')
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def save_xblock_html(self, tmp_dir):
        """
        Saves the XBlock HTML content to a file.
        Generates the 'index.html' file with the HTML added to use it locally.
        Args:
            tmp_dir (str): The temporary directory path to save the xblock content
        """
        html_manipulator = HtmlManipulator(self.xblock, self.html_data, tmp_dir)
        updated_html = html_manipulator.process_html()
        with open(os.path.join(tmp_dir, 'index.html'), 'w') as file:
            file.write(updated_html)

    def create_zip_file(self, temp_dir, base_path, file_name):
        """
        Creates a zip file with the Offline Content in the media storage.
        Args:
            temp_dir (str): The temporary directory path where the content is stored
            base_path (str): The base path directory to save the zip file
            file_name (str): The name of the zip file
        """
        file_path = os.path.join(temp_dir, file_name)
        with ZipFile(file_path, 'w') as zip_file:
            zip_file.write(os.path.join(temp_dir, 'index.html'), 'index.html')
            self.add_files_to_zip_recursively(
                zip_file,
                current_base_path=os.path.join(temp_dir, 'assets'),
                current_path_in_zip='assets',
            )
        with open(file_path, 'rb') as buffered_zip:
            content_file = ContentFile(buffered_zip.read())
            self.storage.save(base_path + file_name, content_file)
        log.info(f'Offline content for {file_name} has been generated.')

    def add_files_to_zip_recursively(self, zip_file, current_base_path, current_path_in_zip):
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
                    self.add_files_to_zip_recursively(zip_file, full_path, full_path_in_zip)
        except OSError:
            log.error(f'Error while reading the directory: {current_base_path}')
            return
