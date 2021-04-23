"""
All the views for our_team app
"""
from django.views.generic import TemplateView

from .models import OurTeamMember


class OurTeamView(TemplateView):
    """
    View to render the our_team page
    """

    template_name = 'adg/lms/our_team/our_team.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        team_members = OurTeamMember.objects.team_members()
        board_of_trustees = OurTeamMember.objects.board_of_trustees()

        context.update({'team_members': team_members, 'board_of_trustees': board_of_trustees})
        return context
