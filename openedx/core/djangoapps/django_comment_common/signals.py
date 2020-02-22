# pylint: disable=invalid-name
"""Signals related to the comments service."""


from django.dispatch import Signal

thread_created = Signal(providing_args=['user', 'post'])
thread_edited = Signal(providing_args=['user', 'post'])
thread_voted = Signal(providing_args=['user', 'post'])
thread_deleted = Signal(providing_args=['user', 'post'])
thread_followed = Signal(providing_args=['user', 'post'])
thread_unfollowed = Signal(providing_args=['user', 'post'])
comment_created = Signal(providing_args=['user', 'post'])
comment_edited = Signal(providing_args=['user', 'post'])
comment_voted = Signal(providing_args=['user', 'post'])
comment_deleted = Signal(providing_args=['user', 'post'])
comment_endorsed = Signal(providing_args=['user', 'post'])
