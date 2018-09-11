"""Signals related to the edxmako rendering methods."""
from django.dispatch import Signal


BEFORE_RENDER_TO_RESPONSE = Signal(providing_args=["template_name", "dictionary", "namespace", "request"])
