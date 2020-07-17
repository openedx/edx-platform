"""
Content libraries related signals.
"""

from django.dispatch import Signal

CONTENT_LIBRARY_CREATED = Signal(providing_args=['library_key'])
CONTENT_LIBRARY_UPDATED = Signal(providing_args=['library_key'])
CONTENT_LIBRARY_DELETED = Signal(providing_args=['library_key'])
LIBRARY_BLOCK_CREATED = Signal(providing_args=['library_key'])
LIBRARY_BLOCK_DELETED = Signal(providing_args=['library_key'])
LIBRARY_BLOCK_UPDATED = Signal(providing_args=['library_key'])
