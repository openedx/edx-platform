"""
API views for badges
"""
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from lms.djangoapps.badges.models import BadgeClass, BadgeAssertion
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus_learning.models import Program, ProgramEnrollment, YearGroup
from openedx.features.genplus_features.genplus_learning.constants import ProgramEnrollmentStatuses, ProgramStatuses
from openedx.features.genplus_features.genplus.api.v1.permissions import IsStudent
from .serializers import ProgramBadgeSerializer


class StudentProgramBadgeView(generics.ListAPIView):

    serializer_class = ProgramBadgeSerializer
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        gen_user = self.request.user.gen_user
        enrolled_programs = ProgramEnrollment.objects\
                                    .filter(student=gen_user.student,
                                            status__in=ProgramEnrollmentStatuses.__VISIBLE__).order_by('created')

        enrolled_year_groups = enrolled_programs.values_list('program__year_group', flat=True).distinct().order_by()
        unenrolled_year_groups = YearGroup.objects.exclude(id__in=enrolled_year_groups)
        unenrolled_active_programs_slug = Program.objects\
                                            .filter(status=ProgramStatuses.ACTIVE, year_group__in=unenrolled_year_groups)\
                                            .values_list('slug', flat=True)
        enrolled_programs_slug = enrolled_programs.values_list('program__slug', flat=True)
        programs_slug = list(enrolled_programs_slug) + list(unenrolled_active_programs_slug)
        queryset = BadgeClass.objects.prefetch_related('badgeassertion_set')\
                                        .filter(issuing_component='genplus__program',
                                                slug__in=programs_slug)
        return queryset

    def get_serializer_context(self):
        context = super(StudentProgramBadgeView, self).get_serializer_context()
        context.update({"user": self.request.user})
        return context
