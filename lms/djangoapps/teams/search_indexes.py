""" Search index used to load data into elasticsearch"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from search.search_engine_base import SearchEngine

from .serializers import CourseTeamSerializer, CourseTeam


class CourseTeamIndexer(object):
    """
    This is the index object for searching and storing CourseTeam model instances.
    """
    INDEX_NAME = "course_team_index"
    DOCUMENT_TYPE_NAME = "course_team"
    ENABLE_SEARCH_KEY = "ENABLE_TEAMS"

    def __init__(self, course_team):
        self.course_team = course_team

    def data(self):
        """
        Uses the CourseTeamSerializer to create a serialized course_team object.
        Adds in additional text and pk fields.
        Removes membership relation.

        Returns serialized object with additional search fields.
        """
        serialized_course_team = CourseTeamSerializer(self.course_team).data
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
        return "{name}\n{description}\n{country}\n{language}".format(
            name=self.course_team.name.encode('utf-8'),
            description=self.course_team.description.encode('utf-8'),
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
    def index(cls, course_team):
        """
        Update index with course_team object (if feature is enabled).
        """
        if cls.search_is_enabled():
            search_engine = cls.engine()
            serialized_course_team = CourseTeamIndexer(course_team).data()
            search_engine.index(cls.DOCUMENT_TYPE_NAME, [serialized_course_team])

    @classmethod
    def engine(cls):
        """
        Return course team search engine (if feature is enabled).
        """
        if cls.search_is_enabled():
            return SearchEngine.get_search_engine(index=cls.INDEX_NAME)

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
    CourseTeamIndexer.index(kwargs['instance'])
