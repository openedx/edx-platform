"""
Typing utilities for the User models.
"""
from __future__ import annotations

import typing as t

import django.contrib.auth.models

User: t.TypeAlias = django.contrib.auth.models.User | django.contrib.auth.models.AnonymousUser
