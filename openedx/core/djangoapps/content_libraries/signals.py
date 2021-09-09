"""
Content libraries related signals.
"""

from django.dispatch import Signal

CONTENT_LIBRARY_CREATED = Signal()
CONTENT_LIBRARY_UPDATED = Signal()
CONTENT_LIBRARY_DELETED = Signal()
LIBRARY_BLOCK_CREATED = Signal()
LIBRARY_BLOCK_DELETED = Signal()
LIBRARY_BLOCK_UPDATED = Signal()
