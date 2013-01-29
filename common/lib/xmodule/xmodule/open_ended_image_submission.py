from PIL import Image

TRUSTED_IMAGE_DOMAINS = [
    'wikipedia.com',
    'wikipedia.net',
    'wikipedia.org'
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

        

