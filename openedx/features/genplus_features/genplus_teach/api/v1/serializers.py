from rest_framework import serializers
from openedx.features.genplus_features.genplus_teach.models import MediaType, Gtcs, Article, ArticleRating, Reflection, \
    ReflectionAnswer, ArticleViewLog, PortfolioEntry, HelpGuideType, HelpGuide, AlertBarEntry, HelpGuideRating, PortfolioReflection
from openedx.features.genplus_features.genplus.api.v1.serializers import SkillSerializer
from openedx.features.genplus_features.common.display_messages import SuccessMessages, ErrorMessages
from openedx.features.genplus_features.common.utils import get_generic_serializer

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
    answer = serializers.SerializerMethodField('get_answer')

    def get_answer(self, instance):
        teacher = self.context.get('teacher')
        try:
            return instance.answers.get(teacher=teacher).answer
        except ReflectionAnswer.DoesNotExist:
            return

    class Meta:
        model = Reflection
        fields = ('id', 'title', 'answer')


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
        teacher = self.context.get('teacher')
        return ReflectionSerializer(instance.reflections.all(),
                                    many=True, context={'teacher': teacher}).data

    class Meta:
        model = Article
        fields = ('id', 'title', 'cover', 'skills', 'gtcs', 'media_types', 'time', 'summary',
                  'content', 'author', 'is_completed', 'is_rated', 'rating', 'reflections', 'created')


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


class PortfolioEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioEntry
        fields = '__all__'

    def perform_create(self, serializer):
        teacher = self.context.get('teacher')
        serializer.save(teacher=teacher)


class GuideRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpGuideRating
        fields = ('rating', 'comment')


class HelpGuideSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()

    def get_rating(self, instance):
        teacher = self.context.get('teacher')
        try:
            guide_rating = HelpGuideRating.objects.get(teacher=teacher, help_guide=instance)
            return GuideRatingSerializer(guide_rating).data
        except HelpGuideRating.DoesNotExist:
            return
    
    class Meta:
        model = HelpGuide
        fields = '__all__'
        depth = 1


class HelpGuideTypeSerializer(serializers.ModelSerializer):
    help_guides = serializers.SerializerMethodField()

    def get_help_guides(self, instance):
        media_type_id = self.context['request'].query_params.get('media_type')
        search = self.context['request'].query_params.get('search')

        items = HelpGuide.objects.filter(guide_type=instance)

        if search:
            items = items.filter(title__icontains=search)
        
        if media_type_id:
            items = items.filter(media_types__id=media_type_id)

        serializer = HelpGuideSerializer(instance=items, many=True)
        return serializer.data

    class Meta:
        model = HelpGuideType
        fields = ('id', 'title', 'help_guides')


class AlertBarEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertBarEntry
        fields = ('id', 'message', 'link')


class ContentObjectRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        if isinstance(value, PortfolioEntry):
            serializer = get_generic_serializer({ 'name': PortfolioEntry, 'fields': '__all__' }, 1)(value)
        elif isinstance(value, ReflectionAnswer):
            serializer = get_generic_serializer({ 'name': ReflectionAnswer, 'fields': '__all__' }, 1)(value)
        else:
            raise Exception('Unexpected type of tagged object')

        return serializer.data


class PortfolioReflectionSerializer(serializers.ModelSerializer):
    content_object = ContentObjectRelatedField(read_only=True)
    entry_type = serializers.CharField(source="content_type.model")

    class Meta:
        model = PortfolioReflection
        fields = ('id', 'created', 'content_object', 'object_id', 'entry_type')
        depth = 2
