from django.core.exceptions import ValidationError


def validate_badge_image(image):
    """
    Validates that a particular image is small enough to be a badge and square.
    """
    if image.width != image.height:
        raise ValidationError("The badge image must be square.")
    if not image.size < (250 * 1024):
        raise ValidationError(
            "The badge image file size must be less than 250KB.")


def validate_lowercase(string):
    """
    Validates that a string is lowercase.
    """
    if not string.islower():
        raise ValidationError("This value must be all lowercase.")


def get_absolute_url(request, file):
    return request.build_absolute_uri(file.url) if file else None
