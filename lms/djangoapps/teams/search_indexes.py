""" Search index used by haystack to load data into elasticsearch"""

from django.conf import settings
from haystack import indexes
from .models import CourseTeam


class CourseTeamIndex(indexes.SearchIndex, indexes.Indexable):
    """
    Index object for CourseTeam model instances
    """
    team_id = indexes.CharField(model_attr='team_id', indexed=False)
    discussion_topic_id = indexes.CharField(model_attr='discussion_topic_id', indexed=False)
    course_id = indexes.CharField(model_attr='course_id', indexed=False)
    topic_id = indexes.CharField(model_attr='topic_id', indexed=False)
    date_created = indexes.DateTimeField(model_attr='date_created')
    is_active = indexes.BooleanField(model_attr='is_active')
    name = indexes.CharField(model_attr='name')
    description = indexes.CharField(model_attr='description')
    country = indexes.CharField(model_attr='country__name')
    language = indexes.CharField(model_attr='language')
    text = indexes.CharField(document=True)

    def get_model(self):
        """
        Returns the model used by this index
        """
        return CourseTeam

    def prepare_language(self, object):
        """
        Convert the language from code to long name
        """
        languages = dict(settings.ALL_LANGUAGES)
        try:
            return languages[object.language]
        except KeyError:
            return object.language

    def prepare_text(self, object):
        """
        Generate the text field used for general search
        """
        return '{name} {description} {country} {language}'.format(
            name=object.name,
            description=object.description,
            country=object.country.name.format(),
            language=self.prepare_language(object)
        )

    def index_queryset(self, using=None):
        """
        Used when the entire index for model is updated.
        """
        return self.get_model().objects.all()

    def get_updated_field(self):
        """
        Get the field name that represents the updated date for the Note model.
        This is used by the reindex command to filter out results from the QuerySet, enabling to reindex only
        recent records. This method returns a string of the Note's field name that contains the date that the model
        was updated.
        """
        return 'date_created'
