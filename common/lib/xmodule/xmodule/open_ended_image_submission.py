from PIL import Image
import urlparse

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

MAX_IMAGE_DIM = 150
MAX_COLORS_TO_COUNT = 16
MAX_COLORS = 5

class ImageProperties(object):
    def __init__(self, image):
        self.image = image
        image_size = self.image.size
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
        image_is_okay = self.count_colors() and self.get_skin_ratio()
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
            if self.url_string.endswith(suffix)
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




