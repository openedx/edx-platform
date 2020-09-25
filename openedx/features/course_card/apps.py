from django.apps import AppConfig


class CourseCardConfig(AppConfig):
    name = u'openedx.features.course_card'

    def ready(self):
        from course_card.models import CourseCard
