"""
Content libraries related signals.
"""

from django.dispatch import Signal

# providing_args=['library_key']
CONTENT_LIBRARY_CREATED = Signal()
# providing_args=['library_key', 'update_blocks']
CONTENT_LIBRARY_UPDATED = Signal()
# providing_args=['library_key']
CONTENT_LIBRARY_DELETED = Signal()

# Same providing_args=['library_key', 'usage_key'] for next 3 signals.
LIBRARY_BLOCK_CREATED = Signal()
LIBRARY_BLOCK_DELETED = Signal()
LIBRARY_BLOCK_UPDATED = Signal()
