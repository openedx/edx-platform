"""
Search index used to load data into elasticsearch.
"""


import logging
from functools import wraps

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import translation
from elasticsearch.exceptions import ConnectionError  # lint-amnesty, pylint: disable=redefined-builtin
from search.search_engine_base import SearchEngine

from lms.djangoapps.teams.models import CourseTeam
from openedx.core.lib.request_utils import get_request_or_stub

from .errors import ElasticSearchConnectionError
from .serializers import CourseTeamSerializer


def if_search_enabled(f):
    """
    Only call `f` if search is enabled for the CourseTeamIndexer.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        """Wraps the decorated function."""
        cls = args[0]
        if cls.search_is_enabled():
            return f(*args, **kwargs)
    return wrapper


class CourseTeamIndexer:
    """
    This is the index object for searching and storing CourseTeam model instances.
    """
    INDEX_NAME = "course_team_index"
    DOCUMENT_TYPE_NAME = "course_team"
    ENABLE_SEARCH_KEY = "ENABLE_TEAMS"
    # Filterable attributes required by Meilisearch when filtering via field_dictionary
    MEILISEARCH_FILTERABLES = [
        "course_id",
        "topic_id",
        "organization_protected",
    ]

    def __init__(self, course_team):
        self.course_team = course_team

    def data(self):
        """
        Uses the CourseTeamSerializer to create a serialized course_team object.
        Adds in additional text and pk fields.
        Removes membership relation.

        Returns serialized object with additional search fields.
        """
        # Django Rest Framework v3.1 requires that we pass the request to the serializer
        # so it can construct hyperlinks.  To avoid changing the interface of this object,
        # we retrieve the request from the request cache.
        context = {
            "request": get_request_or_stub()
        }

        serialized_course_team = CourseTeamSerializer(self.course_team, context=context).data

        # Save the primary key so we can load the full objects easily after we search
        serialized_course_team['pk'] = self.course_team.pk
        # Don't save the membership relations in elasticsearch
        serialized_course_team.pop('membership', None)

        # add generally searchable content
        serialized_course_team['content'] = {
            'text': self.content_text()
        }

        return serialized_course_team

    def content_text(self):
        """
        Generate the text field used for general search.
        """
        # Always use the English version of any localizable strings (see TNL-3239)
        with translation.override('en'):
            return "{name}\n{description}\n{country}\n{language}".format(
                name=self.course_team.name,
                description=self.course_team.description,
                country=self.course_team.country.name.format(),
                language=self._language_name()
            )

    def _language_name(self):
        """
        Convert the language from code to long name.
        """
        languages = dict(settings.ALL_LANGUAGES)
        try:
            return languages[self.course_team.language]
        except KeyError:
            return self.course_team.language

    @classmethod
    @if_search_enabled
    def index(cls, course_team):
        """
        Update index with course_team object (if feature is enabled).
        """
        search_engine = cls.engine()
        serialized_course_team = CourseTeamIndexer(course_team).data()
        search_engine.index([serialized_course_team])

    @classmethod
    @if_search_enabled
    def remove(cls, course_team):
        """
        Remove course_team from the index (if feature is enabled).
        """
        cls.engine().remove([course_team.team_id])

    @classmethod
    @if_search_enabled
    def engine(cls):
        """
        Return course team search engine (if feature is enabled).
        """
        try:
            engine = SearchEngine.get_search_engine(index=cls.INDEX_NAME)
            # If Meilisearch is configured, ensure required filterable attributes
            # are present for this index to avoid invalid_search_filter errors.
            try:
                from django.conf import settings as django_settings
                if getattr(django_settings, "SEARCH_ENGINE", "").endswith(
                    "search.meilisearch.MeilisearchEngine"
                ):
                    # Defer import to avoid hard dependency when not using Meilisearch
                    from search.meilisearch import (
                        get_meilisearch_client,
                        get_meilisearch_index_name,
                        get_or_create_meilisearch_index,
                        update_index_filterables,
                    )

                    client = get_meilisearch_client()
                    meili_index_name = get_meilisearch_index_name(cls.INDEX_NAME)
                    meili_index = get_or_create_meilisearch_index(client, meili_index_name)
                    update_index_filterables(client, meili_index, cls.MEILISEARCH_FILTERABLES)
            except Exception:  # noqa: BLE001 - best-effort safeguard, don't break engine()
                # If any error occurs while ensuring filterables (including if Meilisearch
                # libs are unavailable), proceed without interrupting normal flow.
                pass
            return engine
        except ConnectionError as err:
            logging.error('Error connecting to elasticsearch: %s', err)
            raise ElasticSearchConnectionError  # lint-amnesty, pylint: disable=raise-missing-from

    @classmethod
    def search_is_enabled(cls):
        """
        Return boolean of whether course team indexing is enabled.
        """
        return settings.FEATURES.get(cls.ENABLE_SEARCH_KEY, False)


@receiver(post_save, sender=CourseTeam, dispatch_uid='teams.signals.course_team_post_save_callback')
def course_team_post_save_callback(**kwargs):
    """
    Reindex object after save.
    """
    try:
        CourseTeamIndexer.index(kwargs['instance'])
    except ElasticSearchConnectionError:
        pass


@receiver(post_delete, sender=CourseTeam, dispatch_uid='teams.signals.course_team_post_delete_callback')
def course_team_post_delete_callback(**kwargs):
    """
    Reindex object after delete.
    """
    try:
        CourseTeamIndexer.remove(kwargs['instance'])
    except ElasticSearchConnectionError:
        pass
