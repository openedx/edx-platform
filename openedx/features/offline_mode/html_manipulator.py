"""
Module to prepare HTML content for offline use.
"""
import os
import re
import uuid

from bs4 import BeautifulSoup

from django.conf import settings

from .assets_management import save_asset_file, save_external_file, save_mathjax_to_xblock_assets
from .constants import MATHJAX_CDN_URL, MATHJAX_STATIC_PATH


class HtmlManipulator:
    """
    Class to prepare HTML content for offline use.
    Changes links to static files to paths to pre-generated static files for offline use.
    """

    def __init__(self, xblock, html_data, temp_dir):
        self.html_data = html_data
        self.xblock = xblock
        self.temp_dir = temp_dir

    def process_html(self):
        """
        Prepares HTML content for local usage.
        Changes links to static files to paths to pre-generated static files for offline use.
        """
        self._replace_asset_links()
        self._replace_static_links()
        self._replace_mathjax_link()
        self._replace_external_links()
        self._copy_platform_fonts()

        soup = BeautifulSoup(self.html_data, 'html.parser')
        self._replace_iframe(soup)
        return str(soup)

    def _replace_mathjax_link(self):
        """
        Replace MathJax CDN link with local path to MathJax.js file.
        """
        save_mathjax_to_xblock_assets(self.temp_dir)
        mathjax_pattern = re.compile(fr'src="{MATHJAX_CDN_URL}[^"]*"')
        self.html_data = mathjax_pattern.sub(f'src="{MATHJAX_STATIC_PATH}"', self.html_data)

    def _replace_static_links(self):
        """
        Replace static links with local links.
        """
        static_links_pattern = os.path.join(settings.STATIC_URL, r'[\w./-]+')
        pattern = re.compile(fr'{static_links_pattern}')
        self.html_data = pattern.sub(self._replace_link, self.html_data)

    def _replace_asset_links(self):
        """
        Replace static links with local links.
        """
        pattern = re.compile(r'/assets/[\w./@:+-]+')
        self.html_data = pattern.sub(self._replace_asset_link, self.html_data)

    def _replace_asset_link(self, match):
        """
        Returns the local path of the asset file.
        """
        link = match.group()
        filename = link[1:] if link.startswith('/') else link  # Remove the leading '/'
        save_asset_file(self.temp_dir, self.xblock, link, filename)
        return filename

    def _replace_link(self, match):
        """
        Returns the local path of the asset file.
        """
        link = match.group()
        filename = link.split(settings.STATIC_URL)[-1]
        save_asset_file(self.temp_dir, self.xblock, link, filename)
        return f'assets/{filename}'

    def _replace_external_links(self):
        """
        Replace external links to images and js files with local links.
        """
        pattern = re.compile(r'https:\/\/[^"\s]+?\.(js|jpe?g|png|gif|bmp|svg)')
        self.html_data = pattern.sub(self._replace_external_link, self.html_data)

    def _replace_external_link(self, match):
        """
        Returns the local path of the external file.
        Downloads the external file and saves it to the local directory.
        """
        link = match.group()
        file_extension = match.group(1)
        unique_id = uuid.uuid4()
        filename = f"assets/external/{unique_id}.{file_extension}"
        save_external_file(self.temp_dir, link, filename)

        return filename

    def _copy_platform_fonts(self):
        """
        Copy platform fonts to the block temp directory.
        """
        platform_fonts_dir = "xmodule/js/common_static/fonts/vendor/"
        block_fonts_path = os.path.join(self.temp_dir, "assets", "fonts", "vendor")
        os.makedirs(block_fonts_path)
        for font in os.listdir(platform_fonts_dir):
            font_path = os.path.join(platform_fonts_dir, font)
            if os.path.isfile(font_path):
                os.system(f'cp {font_path} {block_fonts_path}')

    @staticmethod
    def _replace_iframe(soup):
        """
        Replace iframe tags with anchor tags.
        """
        for node in soup.find_all('iframe'):
            replacement = soup.new_tag('p')
            tag_a = soup.new_tag('a')
            tag_a['href'] = node.get('src')
            tag_a.string = node.get('title', node.get('src'))
            replacement.append(tag_a)
            node.replace_with(replacement)
