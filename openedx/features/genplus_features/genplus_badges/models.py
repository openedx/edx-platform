from django.db import models
from django.contrib.auth.models import User
from django_extensions.db.models import TimeStampedModel
from openedx.features.genplus_features.genplus.models import Skill
from openedx.features.genplus_features.genplus_badges.utils import validate_lowercase, validate_badge_image


class BoosterBadge(models.Model):
    slug = models.SlugField(max_length=255, unique=True, validators=[validate_lowercase])
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='booster_badge_classes', validators=[validate_badge_image])

    def __str__(self):
        return f'{self.skill} - {self.display_name}'

    def get_for_user(self, user):
        return self.boosterbadgeaward_set.filter(user=user).first()

    def save(self, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        self.slug = self.slug and self.slug.lower()
        super().save(**kwargs)


class BoosterBadgeAward(TimeStampedModel):
    class Meta:
        unique_together = ('user', 'badge',)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booster_badges')
    badge = models.ForeignKey(BoosterBadge, on_delete=models.CASCADE)
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='teacher_awards')
    feedback = models.TextField(blank=True, default="")
    image_url = models.URLField()

    @classmethod
    def awards_for_user(cls, user):
        return cls.objects.filter(user=user)
