from haystack import indexes
from .models import CourseTeam


class CourseTeamIndex(indexes.SearchIndex, indexes.Indexable):
    team_id = indexes.CharField(model_attr='team_id', indexed=False)
    discussion_topic_id = indexes.CharField(model_attr='discussion_topic_id', indexed=False)
    course_id = indexes.CharField(model_attr='course_id', indexed=False)
    topic_id = indexes.CharField(model_attr='topic_id', indexed=False)
    date_created = indexes.DateTimeField(model_attr='date_created')
    is_active = indexes.BooleanField(model_attr='is_active')
    name = indexes.CharField(model_attr='name')
    description = indexes.CharField(model_attr='description')
    country_code = indexes.CharField(model_attr='country')
    language_code = indexes.CharField(model_attr='language')
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return CourseTeam

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