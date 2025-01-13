"""
Typing utilities for the HTTP requests, responses, etc.

Includes utilties to work with both vanilla django as well as djangorestframework.
"""
from __future__ import annotations

import django.contrib.auth.models  # pylint: disable=imported-auth-user
import django.http
import rest_framework.request

import openedx.core.types.user
from openedx.core.types.meta import type_annotation_only


@type_annotation_only
class HttpRequest(django.http.HttpRequest):
    """
    A request which either has a concrete User (from django.contrib.auth) or is anonymous.
    """
    user: openedx.core.types.User


@type_annotation_only
class AuthenticatedHttpRequest(HttpRequest):
    """
    A request which is guaranteed to have a concrete User (from django.contrib.auth).
    """
    user: django.contrib.auth.models.User


@type_annotation_only
class RestRequest(rest_framework.request.Request):
    """
    Same as HttpRequest, but extended for rest_framework views.
    """
    user: openedx.core.types.User


@type_annotation_only
class AuthenticatedRestRequest(RestRequest):
    """
    Same as AuthenticatedHttpRequest, but extended for rest_framework views.
    """
    user: django.contrib.auth.models.User
