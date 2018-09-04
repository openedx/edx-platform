""" Journal Tab of Learner Dashboard views """
from datetime import datetime, time
import logging

from django.http import Http404

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.features.journals.api import (
    fetch_journal_access,
    journals_enabled,
)


logger = logging.getLogger(__name__)


def journal_listing(request):
    """ View a list of journals which the user has or had access to"""

    user = request.user

    if not journals_enabled() or not user.is_authenticated():
        raise Http404

    journals = fetch_journal_access(
        site=request.site,
        user=request.user
    )

    context = {
        'journals': journals,
        'show_dashboard_tabs': True,
        'show_program_listing': ProgramsApiConfig.is_enabled(),
        'show_journal_listing': journals_enabled()
    }

    return render_to_response('journals/learner_dashboard/journal_dashboard.html', context)


def format_expiration_date(expiration_date):
    """
    Formats Expiration Date

    Arguments:
        expiration_date (str): in format 'YYYY-mm-dd' (ex. April 26, 2018 is: '2018-26-04')

    Returns:
        formatted expiration date (str): in format 'Mmm dd YYYY' (ex. April 26, 2018 is: 'Apr 26 2018')
    """

    # set expiration date to be the last second of the day it expires
    expiration_datetime = datetime.combine(
        date=datetime.strptime(expiration_date, '%Y-%m-%d').date(),
        time=time.max
    )
    return expiration_datetime.strftime("%b %d %Y")


def has_access_expired(expiration_date):
    """
    Returns true if it is now past the expiration date.

    Arguments:
        expiration_date (str): in format 'YYYY-mm-dd' (ex. April 26, 2018 is: '2018-26-04')

    Returns:
        has access expired (boolean): True if access has expired
    """
    # set expiration date to be the last second of the day it expires
    expiration_datetime = datetime.combine(
        date=datetime.strptime(expiration_date, '%Y-%m-%d').date(),
        time=time.max
    )
    now = datetime.today()
    return now > expiration_datetime
