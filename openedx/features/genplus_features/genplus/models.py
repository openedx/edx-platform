from django.conf import settings
from django.db import models
from django_extensions.db.models import TimeStampedModel
from openedx.features.genplus_features.genplus_learning.models import Skill, YearGroup

USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class School(TimeStampedModel):
    guid = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=64)
    external_id = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Class(TimeStampedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classes')
    group_id = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=128)
    year_group = models.ForeignKey(YearGroup, on_delete=models.SET_NULL, null=True, related_name='classes')
    is_visible = models.BooleanField(default=False, help_text='Manage Visibility to Genplus platform')

    def __str__(self):
        return self.name


class Character(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    skills = models.ManyToManyField(Skill, related_name='characters')
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


class GenUser(models.Model):
    STUDENT = 'Student'
    FACULTY = 'Faculty'
    AFFILIATE = 'Affiliate'
    EMPLOYEE = 'Employee'
    TEACHING_STAFF = 'TeachingStaff'
    NON_TEACHING_STAFF = 'NonTeachingStaff'

    user = models.OneToOneField(USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(blank=True, null=True, max_length=32, choices=(
        (STUDENT, 'Student'),
        (FACULTY, 'Faculty'),
        (AFFILIATE, 'Affiliate'),
        (EMPLOYEE, 'Employee'),
        (TEACHING_STAFF, 'TeachingStaff'),
        (NON_TEACHING_STAFF, 'NonTeachingStaff'),
    ))
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True)
    year_of_entry = models.CharField(max_length=32, null=True, blank=True)
    registration_group = models.CharField(max_length=32, null=True, blank=True)

    @property
    def is_student(self):
        return self.role == self.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.TEACHING_STAFF

    def __str__(self):
        return self.user.username


class Teacher(models.Model):
    gen_user = models.OneToOneField(GenUser, on_delete=models.CASCADE, related_name='teacher')
    profile_image = models.ImageField(upload_to='gen_plus_teachers', null=True)
    classes = models.ManyToManyField(Class, related_name='teachers')

    def __str__(self):
        return self.gen_user.user.username


class Student(models.Model):
    gen_user = models.OneToOneField(GenUser, on_delete=models.CASCADE, related_name='student')
    character = models.ForeignKey(Character,on_delete=models.SET_NULL, null=True)
    onboarded = models.BooleanField(default=False)
    year_groups = models.ManyToManyField(YearGroup, related_name='students')

    def __str__(self):
        return self.gen_user.user.username


class TempStudent(TimeStampedModel):
    username = models.CharField(max_length=128, unique=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username
