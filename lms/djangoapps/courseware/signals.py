"""
https://docs.djangoproject.com/en/dev/topics/signals/
"""
import django.dispatch

score_changed = django.dispatch.Signal(providing_args=["user", "course", "score", "problem"])
