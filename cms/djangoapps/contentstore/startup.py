""" will register signal handlers, moved out of __init__.py to ensure correct loading order post Django 1.7 """
from . import signals           # pylint: disable=unused-import
