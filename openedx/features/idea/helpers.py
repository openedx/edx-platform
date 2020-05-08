from django.core.validators import ValidationError

from .constants import IDEA_IMAGE_HEIGHT, IDEA_IMAGE_WIDTH


def upload_to_path(instance, filename, folder):
    """
    Create and return path where files will be uploaded. This path has specific formation
    i.e. app_label/folder/filename
    :param instance: An instance of the model where the FileField is defined
    :param filename: The filename that was originally given to the file
    :param folder: The specific folder where files will be uploaded
    :return: path to upload files
    """
    return '{app_label}/{folder}/{filename}'.format(
        app_label=instance._meta.app_label,
        filename=filename,
        folder=folder
    )


def validate_image_dimensions(image):
    """
    Validate image dimensions, raise validation error if any dimension is invalid.
    :param image: image which is being uploaded
    :return: raise validation error otherwise None
    """
    image_width = getattr(image, 'width', None)
    image_height = getattr(image, 'height', None)

    errors = []

    if image_width and image_width != IDEA_IMAGE_WIDTH:
        errors.append('Width must be {px} px'.format(px=IDEA_IMAGE_WIDTH))

    if image_height and image_height != IDEA_IMAGE_HEIGHT:
        errors.append('Height must be {px} px'.format(px=IDEA_IMAGE_HEIGHT))

    if errors:
        raise ValidationError(', '.join(errors))
