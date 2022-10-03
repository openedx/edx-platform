from rest_framework import serializers
from openedx.features.genplus_features.genplus_teach.models import MediaType, Gtcs, Article, ArticleRating, Reflection, ReflectionAnswer, ArticleViewLog
from openedx.features.genplus_features.genplus.api.v1.serializers import SkillSerializer
from openedx.features.genplus_features.common.display_messages import SuccessMessages, ErrorMessages


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        fields = self.context['request'].query_params.get('fields')
        if fields:
            fields = fields.split(',')
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class GtcsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gtcs
        fields = '__all__'


class MediaTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaType
        fields = '__all__'


class ReflectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reflection
        fields = '__all__'


class ReflectionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReflectionAnswer
        fields = ('answer',)


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReflectionAnswer
        fields = '__all__'
        depth = 2


class ArticleRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleRating
        fields = ('rating', 'comment')


class ArticleSerializer(DynamicFieldsModelSerializer):
    skills = SkillSerializer(read_only=True, many=True)
    gtcs = GtcsSerializer(read_only=True, many=True)
    media_types = MediaTypeSerializer(read_only=True, many=True)
    reflections = serializers.SerializerMethodField('get_reflections')
    is_completed = serializers.SerializerMethodField('get_is_completed')
    is_rated = serializers.SerializerMethodField('get_is_rated')
    rating = serializers.SerializerMethodField('get_rating')
    answer = serializers.SerializerMethodField('get_answer')

    def get_is_completed(self, instance):
        teacher = self.context.get('teacher')
        return instance.is_completed(teacher)

    def get_is_rated(self, instance):
        teacher = self.context.get('teacher')
        return instance.is_rated(teacher)

    def get_rating(self, instance):
        teacher = self.context.get('teacher')
        try:
            return ArticleRatingSerializer(instance.ratings.get(teacher=teacher)).data
        except ArticleRating.DoesNotExist:
            return

    def get_reflections(self, instance):
        return ReflectionSerializer(instance.reflections.all(), many=True).data

    def get_answer(self, instance):
        teacher = self.context.get('teacher')
        try:
            return instance.reflections_answers.get(teacher=teacher).answer
        except ReflectionAnswer.DoesNotExist:
            return

    class Meta:
        model = Article
        fields = ('id', 'title', 'cover', 'skills', 'gtcs', 'media_types', 'time', 'summary',
                  'content', 'author', 'is_completed', 'is_rated', 'rating', 'reflections', 'answer', 'created')


class FavoriteArticleSerializer(serializers.Serializer):
    action = serializers.CharField(max_length=32)

    def validate(self, data):
        if data['action'] not in ['add', 'remove']:
            raise serializers.ValidationError(
                ErrorMessages.ACTION_VALIDATION_ERROR
            )
        return data


class ArticleViewLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleViewLog
        fields = ('count', 'engagement')


