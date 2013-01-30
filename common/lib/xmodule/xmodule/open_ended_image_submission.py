from PIL import Image
import urlparse
import requests
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.conf import settings
import pickle

TRUSTED_IMAGE_DOMAINS = [
    'wikipedia.com',
    'wikipedia.net',
    'wikipedia.org'
]

ALLOWABLE_IMAGE_SUFFIXES = [
    'jpg',
    'png',
    'gif'
]

MAX_ALLOWED_IMAGE_DIM = 400
MAX_IMAGE_DIM = 150
MAX_COLORS_TO_COUNT = 16
MAX_COLORS = 5

class ImageProperties(object):
    def __init__(self, image):
        self.image = image
        image_size = self.image.size
        self.image_too_large = False
        if image_size[0]> MAX_ALLOWED_IMAGE_DIM or image_size[1] > MAX_ALLOWED_IMAGE_DIM:
            self.image_too_large = True
        if image_size[0]> MAX_IMAGE_DIM or image_size[1] > MAX_IMAGE_DIM:
            self.image = self.image.resize((MAX_IMAGE_DIM, MAX_IMAGE_DIM))
            self.image_size = self.image.size

    def count_colors(self):
        colors = self.image.getcolors(MAX_COLORS_TO_COUNT)
        if colors is None:
            colors = MAX_COLORS_TO_COUNT
        else:
            colors = len(colors)

        return colors <= MAX_COLORS

    def get_skin_ratio(self):
        im = self.image
        skin = sum([count for count, rgb in im.getcolors(im.size[0]*im.size[1]) if rgb[0]>60 and rgb[1]<(rgb[0]*0.85) and rgb[2]<(rgb[0]*0.7) and rgb[1]>(rgb[0]*0.4) and rgb[2]>(rgb[0]*0.2)])
        bad_color_val =  float(skin)/float(im.size[0]*im.size[1])
        if bad_color_val > .4:
            is_okay = False
        else:
            is_okay = True
        return is_okay

    def run_tests(self):
        image_is_okay = self.count_colors() and self.get_skin_ratio() and not self.image_too_large
        return image_is_okay

class URLProperties(object):
    def __init__(self, url_string):
        self.url_string = url_string

    def check_if_parses(self):
        success = False
        try:
            self.parsed_url = urlparse.urlparse(url_string)
            success = True
        except:
            pass

        return success

    def check_suffix(self):
        good_suffix = False
        for suffix in ALLOWABLE_IMAGE_SUFFIXES:
            if self.url_string.endswith(suffix):
                good_suffix = True
                break
        return good_suffix

    def run_tests(self):
        url_is_okay = self.check_suffix() and self.check_if_parses()
        return url_is_okay

def run_url_tests(url_string):
    url_properties = URLProperties(url_string)
    return url_properties.run_tests()

def run_image_tests(image):
    image_properties = ImageProperties(image)
    return image_properties.run_tests()

def upload_to_s3(file_to_upload, keyname):
    '''
    Upload file to S3 using provided keyname.

    Returns:
        public_url: URL to access uploaded file
    '''
    try:
        conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucketname = str(settings.AWS_STORAGE_BUCKET_NAME)
        bucket = conn.create_bucket(bucketname.lower())

        k = Key(bucket)
        k.key = keyname
        k.set_metadata('filename', file_to_upload.name)
        k.set_contents_from_file(file_to_upload)
        public_url = k.generate_url(60*60*24*365) # URL timeout in seconds.

        return True, public_url
    except:
        return False, "Could not connect to S3."

def get_from_s3(s3_public_url):
    r = requests.get(s3_public_url, timeout=2)
    data=r.text
    return data

def convert_image_to_string(image):
    return image.tostring()



