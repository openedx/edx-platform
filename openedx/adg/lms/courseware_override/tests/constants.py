"""
Constants for the test files
"""
from datetime import datetime, timedelta

START_DATE = datetime.today() - timedelta(days=365)
END_DATE = datetime.today() + timedelta(days=365)
DUMMY_IMAGE_URLS = {'small': 'small_dummy_url', 'medium': 'large_dummy_url', 'large': 'large_dummy_url'}
