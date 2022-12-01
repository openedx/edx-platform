import re
import logging
import pafy
from django.db import models
from django.db.models import Avg
from django_extensions.db.models import TimeStampedModel
from html import unescape
from django.utils.html import strip_tags
from tinymce.models import HTMLField
from openedx.features.genplus_features.genplus.models import Skill, Teacher
from .constants import AcademicYears


logger = logging.getLogger(__name__)


class Gtcs(TimeStampedModel):
    name = models.CharField(max_length=1024)

    def __str__(self):
        return self.name


class MediaType(models.Model):
    name = models.CharField(unique=True, max_length=255)

    def __str__(self):
        return self.name


class Article(TimeStampedModel):
    ACADEMIC_YEAR_CHOICES = AcademicYears.__MODEL_CHOICES__
    title = models.CharField(max_length=1024)
    cover = models.ImageField(upload_to='article_covers',
                              help_text='Upload the cover for the article')
    skills = models.ManyToManyField(Skill, related_name='articles')
    gtcs = models.ManyToManyField(Gtcs, related_name='articles')
    media_types = models.ManyToManyField(MediaType, related_name='articles')
    summary = HTMLField()
    content = HTMLField()
    author = models.CharField(max_length=1024, help_text='Add name of the author')
    time = models.PositiveIntegerField(default=0, help_text='Time required to read/watch/listen the article')
    academic_year = models.CharField(default=AcademicYears.YEAR_2022_23, max_length=32, choices=ACADEMIC_YEAR_CHOICES)
    is_archived = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    @property
    def favorites_count(self):
        return FavoriteArticle.objects.filter(article=self.id).count()

    @property
    def rating_average(self):
        avg_rating = self.ratings.filter(article=self.id).aggregate(Avg('rating')).get('rating__avg')
        return avg_rating if avg_rating else 0

    def is_completed(self, teacher):
        reflections = self.reflections
        answers = ReflectionAnswer.objects.filter(reflection_id__in=reflections.values_list('id', flat=True),
                                                  teacher=teacher)
        return reflections.count() == answers.count()

    def is_rated(self, teacher):
        return ArticleRating.objects.filter(article=self,
                                            teacher=teacher).exists()

    def is_favorite(self, teacher):
        return teacher.favorite_articles.filter(article=self.pk).count() > 0

    def save(self, **kwargs):
        read_time = self.get_read_time(self.title, self.content)
        watch_time = self.get_video_time(self.content)
        self.time = self.time + read_time + watch_time
        if self.is_featured:
            # marking the other article as non-featured
            Article.objects.filter(is_featured=True).update(is_featured=False)
        super().save(**kwargs)

    @staticmethod
    def get_read_time(title, content):
        string = title + unescape(strip_tags(content))
        total_words = len(string.split())
        return round(total_words / 200)

    def get_video_time(self, content):
        video_time = 0
        links = re.findall(r'(https?://www.youtube.com\S+)', content)
        for link in links:
            watch_link = link.replace('"', ' ').replace('embed/', 'watch?v=')
            video_time += self.get_yt_video_time(watch_link)

        return video_time

    @staticmethod
    def get_yt_video_time(link):
        try:
            video_metadata = pafy.new(link)
            t = 0
            for u in video_metadata.duration.split(':'):
                t = 60 * t + int(u)
            return t/60
        except Exception as e:
            logger.exception(e)
            return 0


class Reflection(TimeStampedModel):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='reflections')
    title = models.TextField()

    def __str__(self):
        return self.title


class ReflectionAnswer(TimeStampedModel):
    reflection = models.ForeignKey(Reflection, on_delete=models.CASCADE, related_name='answers')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    answer = models.TextField()

    class Meta:
        unique_together = ('reflection', 'teacher')


class FavoriteArticle(models.Model):
    MAX_FAVORITE = 10
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='favorite_articles')
    article = models.ForeignKey(Article, on_delete=models.CASCADE)


class ArticleRating(TimeStampedModel):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='ratings')
    rating = models.PositiveIntegerField(default=0)
    comment = models.TextField()

    class Meta:
        unique_together = ('teacher', 'article')

    def __str__(self):
        return '{} has rated {} stars to article {}'.format(
            self.teacher.gen_user.user.get_full_name(),
            self.rating,
            self.article.title
        )


# model to log the view, view count and engagement time on an article
class ArticleViewLog(TimeStampedModel):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='view_logs')
    count = models.PositiveIntegerField(default=0, help_text='Views count on each article.')
    engagement = models.PositiveIntegerField(default=0, help_text='Length of engagement in seconds')

    def __str__(self):
        return '{} has view count {} of "{}" with engagement time of {} seconds'.format(
            self.teacher.gen_user.user.username,
            self.count,
            self.article.title,
            self.engagement
        )


class PortfolioEntry(TimeStampedModel):
    title = models.CharField(max_length=1024)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='portfolio_entries')
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True)
    gtcs = models.ManyToManyField(Gtcs, blank=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Quote(TimeStampedModel):
    banner = models.ImageField(upload_to='quote_banners')
    text = models.TextField()
    author = models.CharField(max_length=1024)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    def save(self, **kwargs):
        if self.is_current:
            # marking the other quote's current false
            Quote.objects.filter(is_current=True).update(is_current=False)
        super().save(**kwargs)


class HelpGuideType(TimeStampedModel):
    title = models.CharField(max_length=1024)

    def __str__(self):
        return self.title


class HelpGuide(TimeStampedModel):
    guide_type = models.ForeignKey(HelpGuideType, on_delete=models.CASCADE)
    title = models.CharField(max_length=1024)
    content = HTMLField()
    media_types = models.ManyToManyField(MediaType, related_name='help_guides')
    time = models.PositiveIntegerField(default=0, help_text='Time required to read/watch/listen the help-guide')

    def __str__(self):
        return self.title


class HelpGuideRating(TimeStampedModel):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    help_guide = models.ForeignKey(HelpGuide, on_delete=models.CASCADE, related_name='ratings')
    rating = models.PositiveIntegerField(default=0)
    comment = models.TextField()

    class Meta:
        unique_together = ('teacher', 'help_guide')

    def __str__(self):
        return '{} has rated {} stars to guide {}'.format(
            self.teacher.gen_user.user.get_full_name(),
            self.rating,
            self.help_guide.title
        )


class AlertBarEntry(TimeStampedModel):
    message = models.TextField()
    link = models.URLField(max_length=1024)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.message

    def save(self, **kwargs):
        if self.is_current:
            # marking the other entry's current false
            AlertBarEntry.objects.filter(is_current=True).update(is_current=False)
        super().save(**kwargs)
