from django.conf import settings
from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from .constants import GenUserRoles, ClassColors, JournalTypes, ActivityTypes

USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class School(TimeStampedModel):
    guid = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=64)
    external_id = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Skill(models.Model):
    name = models.CharField(max_length=128, unique=True)
    image = models.ImageField(upload_to='skill_images', null=True, blank=True)

    def __str__(self):
        return self.name


class Character(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    skills = models.ManyToManyField(Skill, related_name='characters', blank=True)
    profile_pic = models.ImageField(upload_to='gen_plus_avatars',
                                    help_text='Upload the image which will be seen by student on their dashboard')
    standing = models.ImageField(upload_to='gen_plus_avatars',
                                 help_text='Provide standing image of character')
    running = models.ImageField(upload_to='gen_plus_avatars',
                                help_text='Provide running image of character')
    crouching = models.ImageField(upload_to='gen_plus_avatars',
                                  help_text='Provide crouching image of character')
    jumping = models.ImageField(upload_to='gen_plus_avatars',
                                help_text='Provide jumping image of character')

    def __str__(self):
        return self.name


class TempUser(TimeStampedModel):
    """
    To store temporary unregister user data
    """
    username = models.CharField(max_length=128, unique=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class GenUser(models.Model):
    ROLE_CHOICES = GenUserRoles.__MODEL_CHOICES__

    user = models.OneToOneField(USER_MODEL, on_delete=models.CASCADE, null=True, related_name='gen_user')
    role = models.CharField(blank=True, null=True, max_length=32, choices=ROLE_CHOICES)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True)
    year_of_entry = models.CharField(max_length=32, null=True, blank=True)
    registration_group = models.CharField(max_length=32, null=True, blank=True)
    temp_user = models.OneToOneField(TempUser, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def is_student(self):
        return self.role == GenUserRoles.STUDENT

    @property
    def is_teacher(self):
        return self.role == GenUserRoles.TEACHING_STAFF

    def __str__(self):
        return self.user.username


class Student(models.Model):
    gen_user = models.OneToOneField(GenUser, on_delete=models.CASCADE, related_name='student')
    character = models.ForeignKey(Character, on_delete=models.SET_NULL, null=True, blank=True)
    onboarded = models.BooleanField(default=False)

    @property
    def user(self):
        return self.gen_user.user

    def __str__(self):
        return self.user.username


class ClassManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_visible=True)


class Class(TimeStampedModel):
    COLOR_CHOICES = ClassColors.__MODEL_CHOICES__
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classes')
    group_id = models.CharField(primary_key=True, max_length=128)
    color = models.CharField(blank=True, null=True, max_length=32, choices=COLOR_CHOICES)
    image = models.ImageField(upload_to='gen_plus_classes', null=True, blank=True)
    name = models.CharField(max_length=128)
    is_visible = models.BooleanField(default=False, help_text='Manage Visibility to Genplus platform')
    students = models.ManyToManyField(Student, related_name='classes', blank=True)
    program = models.ForeignKey('genplus_learning.Program', on_delete=models.CASCADE, null=True, blank=True, related_name="classes")
    objects = models.Manager()
    visible_objects = ClassManager()

    def __str__(self):
        return self.name


class Teacher(models.Model):
    gen_user = models.OneToOneField(GenUser, on_delete=models.CASCADE, related_name='teacher')
    profile_image = models.ImageField(upload_to='gen_plus_teachers', null=True, blank=True)
    classes = models.ManyToManyField(Class, related_name='teachers', through="genplus.TeacherClass")

    @property
    def user(self):
        return self.gen_user.user

    def __str__(self):
        return self.user.username


class TeacherClass(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    gen_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    is_favorite = models.BooleanField(default=False)


class JournalPost(TimeStampedModel):
    JOURNAL_TYPE_CHOICES = JournalTypes.__MODEL_CHOICES__
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="journal_posts")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, related_name="journal_feedbacks")
    title = models.CharField(max_length=128)
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    type = models.CharField(max_length=32, choices=JOURNAL_TYPE_CHOICES)


class ActivityManager(models.Manager):
    def student_activities(self, student_id=None):
        return super().get_queryset().filter(target_content_type__model='student', target_object_id=student_id)


class Activity(TimeStampedModel):
    ACTIVITY_TYPE = ActivityTypes.__MODEL_CHOICES__

    # Actor: The object that performed the activity.
    actor_content_type = models.ForeignKey(
        ContentType, related_name='actor', blank=True, null=True,
        on_delete=models.CASCADE, db_index=True
    )
    actor_object_id = models.CharField(max_length=255, db_index=True)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    # Type: the type of activity perform
    type = models.CharField(max_length=128, choices=ACTIVITY_TYPE)

    # Target: The object to which the activity was performed
    target_content_type = models.ForeignKey(
        ContentType, blank=True, null=True,
        related_name='target',
        on_delete=models.CASCADE, db_index=True
    )
    target_object_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    target = GenericForeignKey(
        'target_content_type',
        'target_object_id'
    )
    # Action : The object linked to the action itself
    action_object_content_type = models.ForeignKey(
        ContentType, blank=True, null=True,
        related_name='action_object',
        on_delete=models.CASCADE, db_index=True
    )
    action_object_object_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )
    action_object = GenericForeignKey(
        'action_object_content_type',
        'action_object_object_id'
    )
    objects = ActivityManager()
