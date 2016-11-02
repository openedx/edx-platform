"""
This is the local_settings file for platform API doc.
"""

# Generate a SECRET_KEY for this build
from random import choice
characters = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
SECRET_KEY = ''.join([choice(characters) for i in range(50)])

# for use in openedx/core/djangoapps/profile_images/images.py
PROFILE_IMAGE_MAX_BYTES = 1000
PROFILE_IMAGE_MIN_BYTES = 1000
