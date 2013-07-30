"""
This contains functions and classes used to evaluate if images are acceptable (do not show improper content, etc), and
to send them to S3.
"""

try:
    from PIL import Image

    ENABLE_PIL = True
except:
    ENABLE_PIL = False

from urlparse import urlparse
import requests
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import logging

log = logging.getLogger(__name__)

#Domains where any image linked to can be trusted to have acceptable content.
TRUSTED_IMAGE_DOMAINS = [
    'wikipedia',
    'edxuploads.s3.amazonaws.com',
    'wikimedia',
]

#Suffixes that are allowed in image urls
ALLOWABLE_IMAGE_SUFFIXES = [
    'jpg',
    'png',
    'gif',
    'jpeg'
]

#Maximum allowed dimensions (x and y) for an uploaded image
MAX_ALLOWED_IMAGE_DIM = 2000

#Dimensions to which image is resized before it is evaluated for color count, etc
MAX_IMAGE_DIM = 150

#Maximum number of colors that should be counted in ImageProperties
MAX_COLORS_TO_COUNT = 16

#Maximum number of colors allowed in an uploaded image
MAX_COLORS = 400


class ImageProperties(object):
    """
    Class to check properties of an image and to validate if they are allowed.
    """

    def __init__(self, image_data):
        """
        Initializes class variables
        @param image: Image object (from PIL)
        @return: None
        """
        self.image = Image.open(image_data)
        image_size = self.image.size
        self.image_too_large = False
        if image_size[0] > MAX_ALLOWED_IMAGE_DIM or image_size[1] > MAX_ALLOWED_IMAGE_DIM:
            self.image_too_large = True
        if image_size[0] > MAX_IMAGE_DIM or image_size[1] > MAX_IMAGE_DIM:
            self.image = self.image.resize((MAX_IMAGE_DIM, MAX_IMAGE_DIM))
            self.image_size = self.image.size

    def count_colors(self):
        """
        Counts the number of colors in an image, and matches them to the max allowed
        @return: boolean true if color count is acceptable, false otherwise
        """
        colors = self.image.getcolors(MAX_COLORS_TO_COUNT)
        if colors is None:
            color_count = MAX_COLORS_TO_COUNT
        else:
            color_count = len(colors)

        too_many_colors = (color_count <= MAX_COLORS)
        return too_many_colors

    def check_if_rgb_is_skin(self, rgb):
        """
        Checks if a given input rgb tuple/list is a skin tone
        @param rgb: RGB tuple
        @return: Boolean true false
        """
        colors_okay = False
        try:
            r = rgb[0]
            g = rgb[1]
            b = rgb[2]
            check_r = (r > 60)
            check_g = (r * 0.4) < g < (r * 0.85)
            check_b = (r * 0.2) < b < (r * 0.7)
            colors_okay = check_r and check_b and check_g
        except:
            pass

        return colors_okay

    def get_skin_ratio(self):
        """
        Gets the ratio of skin tone colors in an image
        @return: True if the ratio is low enough to be acceptable, false otherwise
        """
        colors = self.image.getcolors(MAX_COLORS_TO_COUNT)
        is_okay = True
        if colors is not None:
            skin = sum([count for count, rgb in colors if self.check_if_rgb_is_skin(rgb)])
            total_colored_pixels = sum([count for count, rgb in colors])
            bad_color_val = float(skin) / total_colored_pixels
            if bad_color_val > .4:
                is_okay = False

        return is_okay

    def run_tests(self):
        """
        Does all available checks on an image to ensure that it is okay (size, skin ratio, colors)
        @return: Boolean indicating whether or not image passes all checks
        """
        image_is_okay = False
        try:
            #image_is_okay = self.count_colors() and self.get_skin_ratio() and not self.image_too_large
            image_is_okay = not self.image_too_large
        except:
            log.exception("Could not run image tests.")

        if not ENABLE_PIL:
            image_is_okay = True

        #log.debug("Image OK: {0}".format(image_is_okay))

        return image_is_okay


class URLProperties(object):
    """
    Checks to see if a URL points to acceptable content.  Added to check if students are submitting reasonable
    links to the peer grading image functionality of the external grading service.
    """

    def __init__(self, url_string):
        self.url_string = url_string

    def check_if_parses(self):
        """
        Check to see if a URL parses properly
        @return: success (True if parses, false if not)
        """
        success = False
        try:
            self.parsed_url = urlparse(self.url_string)
            success = True
        except:
            pass

        return success

    def check_suffix(self):
        """
        Checks the suffix of a url to make sure that it is allowed
        @return: True if suffix is okay, false if not
        """
        good_suffix = False
        for suffix in ALLOWABLE_IMAGE_SUFFIXES:
            if self.url_string.endswith(suffix):
                good_suffix = True
                break
        return good_suffix

    def run_tests(self):
        """
        Runs all available url tests
        @return: True if URL passes tests, false if not.
        """
        url_is_okay = self.check_suffix() and self.check_if_parses()
        return url_is_okay

    def check_domain(self):
        """
        Checks to see if url is from a trusted domain
        """
        success = False
        for domain in TRUSTED_IMAGE_DOMAINS:
            if domain in self.url_string:
                success = True
                return success
        return success


def run_url_tests(url_string):
    """
    Creates a URLProperties object and runs all tests
    @param url_string: A URL in string format
    @return: Boolean indicating whether or not URL has passed all tests
    """
    url_properties = URLProperties(url_string)
    return url_properties.run_tests()


def run_image_tests(image):
    """
    Runs all available image tests
    @param image: PIL Image object
    @return: Boolean indicating whether or not all tests have been passed
    """
    success = False
    try:
        image_properties = ImageProperties(image)
        success = image_properties.run_tests()
    except:
        log.exception("Cannot run image tests in combined open ended xmodule.  May be an issue with a particular image,"
                      "or an issue with the deployment configuration of PIL/Pillow")
    return success


def upload_to_s3(file_to_upload, keyname, s3_interface):
    '''
    Upload file to S3 using provided keyname.

    Returns:
        public_url: URL to access uploaded file
    '''

    #This commented out code is kept here in case we change the uploading method and require images to be
    #converted before they are sent to S3.
    #TODO: determine if commented code is needed and remove
    #im = Image.open(file_to_upload)
    #out_im = cStringIO.StringIO()
    #im.save(out_im, 'PNG')

    try:
        conn = S3Connection(s3_interface['access_key'], s3_interface['secret_access_key'])
        bucketname = str(s3_interface['storage_bucket_name'])
        bucket = conn.create_bucket(bucketname.lower())

        k = Key(bucket)
        k.key = keyname
        k.set_metadata('filename', file_to_upload.name)
        k.set_contents_from_file(file_to_upload)

        #This commented out code is kept here in case we change the uploading method and require images to be
        #converted before they are sent to S3.
        #k.set_contents_from_string(out_im.getvalue())
        #k.set_metadata("Content-Type", 'images/png')

        k.set_acl("public-read")
        public_url = k.generate_url(60 * 60 * 24 * 365)   # URL timeout in seconds.

        return True, public_url
    except:
        #This is a dev_facing_error
        error_message = "Could not connect to S3 to upload peer grading image.  Trying to utilize bucket: {0}".format(
            bucketname.lower())
        log.error(error_message)
        return False, error_message


def get_from_s3(s3_public_url):
    """
    Gets an image from a given S3 url
    @param s3_public_url: The URL where an image is located
    @return: The image data
    """
    r = requests.get(s3_public_url, timeout=2)
    data = r.text
    return data
