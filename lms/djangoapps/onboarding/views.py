"""
Views for on-boarding app.
"""
import base64
import json
import logging
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.views.decorators.csrf import csrf_exempt

from edxmako.shortcuts import render_to_response
from lms.djangoapps.onboarding import forms
from lms.djangoapps.onboarding.decorators import can_save_org_data, can_save_org_details
from lms.djangoapps.onboarding.email_utils import (
    send_admin_activation_email,
    send_admin_update_confirmation_email,
    send_admin_update_email
)
from lms.djangoapps.onboarding.helpers import (
    COUNTRIES,
    LANGUAGES,
    affiliated_unattended_surveys,
    calculate_age_years,
    get_alquity_community_url,
    get_close_matching_orgs_with_suggestions,
    serialize_partner_networks
)
from lms.djangoapps.onboarding.models import (
    Currency,
    Organization,
    OrganizationAdminHashKeys,
    OrganizationMetric,
    PartnerNetwork,
    UserExtendedProfile
)
from lms.djangoapps.onboarding.serializers import PartnerNetworkSerializer
from lms.djangoapps.onboarding.signals import save_interests
from lms.djangoapps.philu_overrides.helpers import save_user_partner_network_consent
from lms.djangoapps.student_dashboard.views import get_joined_communities, get_recommended_xmodule_courses
from nodebb.helpers import update_nodebb_for_user_status
from student.models import PendingEmailChange

log = logging.getLogger("edx.onboarding")


@login_required
@transaction.atomic
def user_info(request):
    """
    The view to handle user info survey from the user.

    If its a GET request then an empty form for survey is returned
    otherwise, a form is populated form the POST request data and
    is then saved. After saving the form, user is redirected to the
    next survey namely, interests survey.
    """

    user_extended_profile = request.user.extended_profile
    are_forms_complete, unattended_org_surveys = affiliated_unattended_surveys(user_extended_profile)
    userprofile = request.user.profile
    is_under_age = False
    reset_org = False
    is_poc = user_extended_profile.is_organization_admin

    template = 'onboarding/tell_us_more_survey.html'

    if request.path == reverse('additional_information'):
        template = 'myaccount/additional_information.html'

    initial = {
        'year_of_birth': userprofile.year_of_birth,
        'gender': userprofile.gender,
        'language': userprofile.language,
        'country': COUNTRIES.get(userprofile.country) if not request.POST.get('country') else request.POST.get(
            'country'),
        'country_of_employment': COUNTRIES.get(user_extended_profile.country_of_employment, '') if not request.POST.get(
            'country_of_employment') else request.POST.get('country_of_employment'),
        'city': userprofile.city,
        'level_of_education': userprofile.level_of_education,
        'hours_per_week': user_extended_profile.hours_per_week if user_extended_profile.hours_per_week else '',
        'is_emp_location_different': True if user_extended_profile.country_of_employment else False,
        'organization_name': user_extended_profile.organization.label if user_extended_profile.organization else "",
        'is_poc': "1" if user_extended_profile.is_organization_admin else "0",
        'is_currently_employed': request.POST.get('is_currently_employed'),
        'org_admin_email':
            user_extended_profile.organization.unclaimed_org_admin_email if user_extended_profile.organization else "",
        'role_in_org': user_extended_profile.role_in_org if user_extended_profile.role_in_org else ""
    }

    context = {
        'are_forms_complete': are_forms_complete, 'first_name': request.user.first_name,
        'fields_to_disable': []
    }

    year_of_birth = userprofile.year_of_birth

    if request.method == 'POST':
        year_of_birth = request.POST.get('year_of_birth')

    if year_of_birth:
        years = calculate_age_years(int(year_of_birth))
        if years < 16:
            is_under_age = True

    if request.method == 'POST':
        form = forms.UserInfoModelForm(request.POST, instance=user_extended_profile, initial=initial)

        if form.is_valid() and not is_under_age:
            custom_model = form.save(request)

            if custom_model.organization:
                custom_model.organization.save()

            return redirect(reverse("additional_information"))
        else:
            reset_org = True
            is_poc = True if request.POST.get('is_poc') == '1' else False
            initial['is_poc'] = is_poc

    else:
        form = forms.UserInfoModelForm(instance=user_extended_profile, initial=initial)

    context.update({
        'form': form,
        'is_under_age': is_under_age,
        'non_profile_organization': Organization.is_non_profit(user_extended_profile),
        'is_poc': is_poc,
        'is_first_user': user_extended_profile.is_first_signup_in_org if user_extended_profile.organization else False,
        'google_place_api_key': settings.GOOGLE_PLACE_API_KEY,
        'org_url': reverse('get_organizations'),
        'reset_org': reset_org,
        'is_employed': bool(user_extended_profile.organization),
        'partners_opt_in': request.POST.get('partners_opt_in', ''),
        'unattended_org_surveys': unattended_org_surveys,
    })

    context.update(user_extended_profile.unattended_surveys())
    return render(request, template, context)


@login_required
@transaction.atomic
def interests(request):
    """
    The view to handle interests survey from the user.

    If its a GET request then an empty form for survey is returned
    otherwise, a form is populated form the POST request and then is
    saved. After saving the form, user is redirected to the next survey
    namely, organization survey.
    """
    user_extended_profile = request.user.extended_profile
    are_forms_complete, unattended_org_surveys = affiliated_unattended_surveys(user_extended_profile)
    is_first_signup_in_org = user_extended_profile.is_first_signup_in_org \
        if user_extended_profile.organization else False

    template = 'onboarding/interests_survey.html'

    if request.path == reverse('update_interests'):
        template = 'myaccount/interests.html'

    if request.method == 'POST':
        form = forms.InterestsModelForm(request.POST, instance=user_extended_profile)

        is_action_update = user_extended_profile.is_interests_data_submitted
        form.save(request)
        save_interests.send(sender=UserExtendedProfile, instance=user_extended_profile)

        are_forms_complete = not (bool(user_extended_profile.unattended_surveys(_type='list')))

        if are_forms_complete and not is_action_update:
            update_nodebb_for_user_status(request.user.username)

    else:
        form = forms.InterestsModelForm(instance=user_extended_profile)
    context = {'form': form, 'are_forms_complete': are_forms_complete}

    user = request.user
    extended_profile = user.extended_profile
    context.update(extended_profile.unattended_surveys())

    context.update({
        'non_profile_organization': Organization.is_non_profit(user_extended_profile),
        'is_poc': extended_profile.is_organization_admin,
        'is_first_user': is_first_signup_in_org,
        'unattended_org_surveys': unattended_org_surveys,
    })

    return render(request, template, context)


@login_required
@can_save_org_data
@transaction.atomic
def organization(request):
    """
    The view to handle organization survey from the user.

    If its a GET request then an empty form for survey is returned
    otherwise, a form is populated form the POST request and then is
    saved. After saving the form, user is redirected to recommendations page.
    """

    user_extended_profile = request.user.extended_profile
    _organization = user_extended_profile.organization
    are_forms_complete, unattended_org_surveys = affiliated_unattended_surveys(user_extended_profile)

    template = 'onboarding/organization_survey.html'
    redirect_to_next = True
    is_my_account_page = False

    if request.path == reverse('myaccount_organization'):
        if not unattended_org_surveys:
            raise PermissionDenied

        is_my_account_page = True
        template = 'organization/update_organization.html'

    if request.path == reverse('update_organization'):
        redirect_to_next = False
        template = 'organization/update_organization.html'

    initial = {
        'country': COUNTRIES.get(_organization.country),
        'is_org_url_exist': '1' if _organization.url else '0',
        'partner_networks': list(_organization.get_active_partners()),
    }

    if request.method == 'POST':
        old_url = request.POST.get('url', '').replace('http://', 'https://', 1)
        form = forms.OrganizationInfoForm(request.POST, instance=_organization, initial=initial)

        if form.is_valid():
            form.save(request)
            old_url = _organization.url.replace('https://', '', 1) if _organization.url else _organization.url
            are_forms_complete, unattended_org_surveys = affiliated_unattended_surveys(user_extended_profile)

            if unattended_org_surveys:
                # redirect to organization detail page
                if redirect_to_next and not is_my_account_page:
                    return redirect(reverse('org_detail_survey'))
            else:
                # update nodebb for user profile completion
                update_nodebb_for_user_status(request.user.username)

                if is_my_account_page:
                    return redirect(reverse('recommendations'))

                if redirect_to_next and user_extended_profile.is_alquity_user:
                    return redirect(get_alquity_community_url())

    else:
        old_url = _organization.url.replace('https://', '', 1) if _organization.url else _organization.url
        form = forms.OrganizationInfoForm(instance=_organization, initial=initial)

    context = {'form': form, 'are_forms_complete': are_forms_complete, 'old_url': old_url}

    organization = user_extended_profile.organization
    context.update(user_extended_profile.unattended_surveys())

    context.update({
        'non_profile_organization': Organization.is_non_profit(user_extended_profile),
        'is_poc': user_extended_profile.is_organization_admin,
        'is_first_user': user_extended_profile.is_first_signup_in_org if user_extended_profile.organization else False,
        'org_admin_id': organization.admin_id if user_extended_profile.organization else None,
        'organization_name': _organization.label,
        'google_place_api_key': settings.GOOGLE_PLACE_API_KEY,
        'partner_networks': serialize_partner_networks(),
        'partners_opt_in': request.POST.get('partners_opt_in', ''),
        'is_my_account_page': is_my_account_page,
        'unattended_org_surveys': unattended_org_surveys,
    })

    return render(request, template, context)


@login_required
def delete_my_account(request):
    user = request.user

    try:
        logout(request)
        user = User.objects.get(id=user.id)
        user.delete()
        data = json.dumps({"status": 200})
    except User.DoesNotExist:
        log.info("User does not exists")
        data = json.dumps({"status": 200})

    mime_type = 'application/json'
    return HttpResponse(data, mime_type)


@csrf_exempt
def get_country_names(request):
    """
    Returns country names.
    """
    if request.is_ajax():
        q = request.GET.get('term', '')
        all_countries = COUNTRIES.values()

        filtered_countries = [country for country in all_countries if country.lower().startswith(q.lower())]

        data = json.dumps(filtered_countries)

    else:
        data = 'fail'

    mime_type = 'application/json'

    return HttpResponse(data, mime_type)


@login_required
@can_save_org_details
@transaction.atomic
def org_detail_survey(request):
    user_extended_profile = request.user.extended_profile
    are_forms_complete, unattended_org_surveys = affiliated_unattended_surveys(user_extended_profile)
    latest_survey = OrganizationMetric.objects.filter(org=user_extended_profile.organization).last()

    initial = {
        'actual_data': '1' if latest_survey and latest_survey.actual_data else '0',
        'registration_number': user_extended_profile.organization.registration_number if user_extended_profile.organization else '',
        "effective_date": datetime.strftime(latest_survey.effective_date, '%m/%d/%Y') if latest_survey else ""
    }

    template = 'onboarding/organization_detail_survey.html'
    next_page_url = reverse('recommendations')
    org_metric_form = forms.OrganizationMetricModelForm
    redirect_to_next = True
    is_my_account_page = False

    if request.path == reverse('myaccount_organization_detail'):
        is_my_account_page = True
        if not unattended_org_surveys:
            raise PermissionDenied

    if request.path == reverse('update_organization_details'):
        redirect_to_next = False
        template = 'organization/update_organization_details.html'
        org_metric_form = forms.OrganizationMetricModelUpdateForm

    if request.method == 'POST':
        available_next = request.POST.get('next', None)
        is_user_coming_from_overlay = available_next and available_next == 'oef'
        if is_user_coming_from_overlay:
            redirect_to_next = True

        if latest_survey:
            form = org_metric_form(request.POST, instance=latest_survey, initial=initial)
        else:
            form = org_metric_form(request.POST, initial=initial)

        if form.is_valid():
            form.save(request)

            are_forms_complete, unattended_org_surveys = affiliated_unattended_surveys(user_extended_profile)

            if is_my_account_page and not unattended_org_surveys:
                update_nodebb_for_user_status(request.user.username)
                return redirect(next_page_url)
            elif are_forms_complete and redirect_to_next:
                update_nodebb_for_user_status(request.user.username)
                if user_extended_profile.is_alquity_user:
                    next_page_url = get_alquity_community_url()
                if is_user_coming_from_overlay:
                    next_page_url = reverse('oef_dashboard')

                return redirect(next_page_url)

    else:
        if latest_survey:
            form = org_metric_form(instance=latest_survey, initial=initial)
        else:
            form = org_metric_form()

    next_url = request.GET.get('next', None)
    context = {'form': form, 'are_forms_complete': are_forms_complete, 'next': next_url}
    context.update(user_extended_profile.unattended_surveys())

    context.update({
        'non_profile_organization': Organization.is_non_profit(user_extended_profile),
        'is_poc': user_extended_profile.is_organization_admin,
        'is_first_user': user_extended_profile.is_first_signup_in_org if user_extended_profile.organization else False,
        'organization_name': user_extended_profile.organization.label,
        'is_my_account_page': is_my_account_page,
        'unattended_org_surveys': unattended_org_surveys,
    })

    return render(request, template, context)


@csrf_exempt
def get_languages(request):
    """
    Returns languages
    """
    if request.is_ajax():
        q = request.GET.get('term', '')
        filtered_languages = [language for language in LANGUAGES if language.lower().startswith(q.lower())]
        data = json.dumps(filtered_languages)
    else:
        data = 'fail'

    mime_type = 'application/json'

    return HttpResponse(data, mime_type)


@login_required
def update_account_settings(request):
    """
    View to handle update of registration extra fields
    """
    from lms.djangoapps.onboarding.helpers import get_user_on_demand_courses, get_email_pref_on_demand_course

    user_extended_profile = UserExtendedProfile.objects.get(user_id=request.user.id)
    partners_opt_in = request.POST.get('partners_opt_in', '')

    on_demand_courses = get_user_on_demand_courses(request.user)

    first_on_demand_course_email_preference = get_email_pref_on_demand_course(
        request.user, on_demand_courses[0].id) if len(on_demand_courses) > 0 else True
    on_demand_courses_options = [(course.id, str(course.display_name)) for course in on_demand_courses]

    if request.method == 'POST':

        form = forms.UpdateRegModelForm(
            on_demand_courses_options,
            first_on_demand_course_email_preference,
            request.POST,
            instance=user_extended_profile)
        if form.is_valid():
            user_extended_profile = form.save(user=user_extended_profile.user, commit=True)
            save_user_partner_network_consent(user_extended_profile.user, partners_opt_in)

            return redirect(reverse('update_account_settings'))

    else:
        email_preferences = getattr(request.user, 'email_preferences', None)

        form = forms.UpdateRegModelForm(
            on_demand_courses_options,
            first_on_demand_course_email_preference,
            instance=user_extended_profile,
            initial={
                'organization_name': user_extended_profile.organization.label if user_extended_profile.organization else "",
                'is_poc': "1" if user_extended_profile.is_organization_admin else "0",
                'first_name': user_extended_profile.user.first_name,
                'last_name': user_extended_profile.user.last_name,
                'opt_in': email_preferences.opt_in if email_preferences else ''
            }
        )

    _, unattended_org_surveys = affiliated_unattended_surveys(user_extended_profile)

    pending_new_email = ''
    is_email_change_pending = False
    pending_email_change = PendingEmailChange.objects.filter(user=request.user).first()
    if pending_email_change:
        is_email_change_pending = True
        pending_new_email = pending_email_change.new_email

    ctx = {
        'form': form,
        'admin_has_pending_admin_suggestion_request': user_extended_profile.admin_has_pending_admin_suggestion_request(),
        'org_url': reverse('get_organizations'),
        'partners_opt_in': partners_opt_in,
        'is_email_change_pending': is_email_change_pending,
        'pending_new_email': pending_new_email,
        'is_poc': user_extended_profile.is_organization_admin,
        'is_first_user': user_extended_profile.is_first_signup_in_org if user_extended_profile.organization else False,
        'non_profile_organization': Organization.is_non_profit(user_extended_profile),
        'unattended_org_surveys': unattended_org_surveys,
    }

    return render(request, 'myaccount/registration_update.html', ctx)


@login_required
def suggest_org_admin(request):
    """
    Suggest a user as administrator of an organization
    """
    status = 200
    message = 'E-mail successfully sent.'

    if request.method == 'POST':
        organization = request.POST.get('organization')
        org_admin_email = request.POST.get('email')
        try:
            org_admin_first_name = User.objects.get(email=org_admin_email).first_name
        except:
            org_admin_first_name = ''

        if organization:
            try:
                organization = Organization.objects.get(label__iexact=organization)
                extended_profile = request.user.extended_profile

                if org_admin_email:
                    already_an_admin = Organization.objects.filter(admin__email=org_admin_email).first()

                    already_suggested_as_admin = OrganizationAdminHashKeys.objects.filter(
                        suggested_admin_email=org_admin_email, is_hash_consumed=False).first()

                    if already_an_admin:
                        status = 400
                        message = ugettext_noop('%s is already admin of organization "%s"'
                                                % (org_admin_email, already_an_admin.label))
                    elif already_suggested_as_admin:
                        message = ugettext_noop('%s is already suggested as admin of "%s" organization'
                                                % (org_admin_email, already_suggested_as_admin.organization.label))
                    else:
                        hash_key = OrganizationAdminHashKeys.assign_hash(organization, request.user, org_admin_email)
                        org_id = extended_profile.organization_id
                        org_name = extended_profile.organization.label
                        organization.unclaimed_org_admin_email = org_admin_email
                        claimed_by_name = "{first_name} {last_name}".format(first_name=request.user.first_name,
                                                                            last_name=request.user.last_name)
                        claimed_by_email = request.user.email

                        send_admin_activation_email(org_admin_first_name, org_id, org_name, claimed_by_name,
                                                    claimed_by_email, org_admin_email, hash_key)
                else:
                    hash_key = OrganizationAdminHashKeys.assign_hash(organization, organization.admin,
                                                                     request.user.email)
                    send_admin_update_email(organization.id, organization.label, organization.admin.email,
                                            organization.admin.first_name, hash_key, request.user.email,
                                            request.user.username
                                            )

            except Organization.DoesNotExist:
                log.info("Organization does not exists: %s" % organization)
                status = 400
            except Exception as ex:
                log.info(ex.args)
                status = 400

    return JsonResponse({'status': status, 'message': message})


@csrf_exempt
def get_organizations(request):
    """
    Get organizations
    """
    final_result = {}

    if request.is_ajax():
        query = request.GET.get('term', '')

        final_result = get_close_matching_orgs_with_suggestions(request, query)

        if request.user.is_authenticated():
            user_extended_profile = request.user.extended_profile
            org = user_extended_profile.organization

            if org:
                _result = {
                    'org': org.label,
                    'is_poc': True if org.admin == request.user else False,
                    'admin_email': org.admin.email if org.admin else ''
                }
            else:
                _result = {
                    'org': '',
                    'is_poc': False,
                    'admin_email': ''
                }

            final_result['user_org_info'] = _result

    return JsonResponse(final_result)


@csrf_exempt
def get_currencies(request):
    currencies = []

    if request.is_ajax():
        term = request.GET.get('term', '')
        currencies = Currency.objects.filter(Q(country__icontains=term) | Q(name__icontains=term) |
                                             Q(alphabetic_code__icontains=term)).values_list('alphabetic_code',
                                                                                             flat=True).distinct()
    data = json.dumps(list(currencies))
    return HttpResponse(data, 'application/json')


@login_required
def recommendations(request):
    """
    Display recommended courses and communities based on the survey

    """
    recommended_courses = get_recommended_xmodule_courses(request)
    joined_communities = get_joined_communities(request.user)

    context = {
        'recommended_courses': recommended_courses,
        'joined_communities': joined_communities,
    }

    return render_to_response('onboarding/recommendations.html', context)


@csrf_exempt
@transaction.atomic
def admin_activation(request, activation_key):
    """
        When clicked on link sent in email to make user admin.

        activation_status can have values 1, 2, 3, 4, 5.
        1 = Activated
        2 = Already Active
        3 = Invalid Hash
        4 = To be Activated
        5 = User not exist in platform

    """
    hash_key = None
    context = {
        'is_org_admin': False
    }

    admin_activation = True if request.GET.get('admin_activation') == 'True' else False

    try:
        hash_key = OrganizationAdminHashKeys.objects.get(activation_hash=activation_key)
        admin_change_confirmation = True if request.GET.get('confirm') == 'True' else False
        current_admin = hash_key.organization.admin
        user_extended_profile = UserExtendedProfile.objects.get(user__email=hash_key.suggested_admin_email)
        new_admin = user_extended_profile.user

        context['key'] = hash_key.activation_hash
        context['is_org_admin'] = True if hash_key.suggested_by == current_admin else False

        if hash_key.is_hash_consumed:
            activation_status = 2
        else:
            activation_status = 4

        # Proceed only if hash_key is not already consumed
        if request.method == 'POST' and activation_status != 2:
            hash_key.is_hash_consumed = True
            hash_key.save()
            # Consume all entries of hash keys where suggested_admin_email = hash_key.suggested_admin_email,
            # so he can not use those links in future
            unconsumed_hash_keys = OrganizationAdminHashKeys.objects.filter(
                is_hash_consumed=False, suggested_admin_email=hash_key.suggested_admin_email
            )
            if unconsumed_hash_keys:
                unconsumed_hash_keys.update(is_hash_consumed=True)

            # Change the admin of the organization if admin is being activated or updated on user confirmation[True]
            if admin_activation or admin_change_confirmation:

                # If claimer's is admin of some other organization remove his privileges
                # for that organization as he can only be an admin of single organization
                if user_extended_profile.organization and user_extended_profile.organization.admin == new_admin:
                    user_extended_profile.organization.admin = None
                    user_extended_profile.organization.save()

                hash_key.organization.unclaimed_org_admin_email = None
                hash_key.organization.admin = new_admin
                hash_key.organization.save()

                # Update the claimer's organization if a user confirms
                user_extended_profile.organization = hash_key.organization
                user_extended_profile.save()
                activation_status = 1

            if not admin_activation:
                # Send an email to claimer, on admin updation depending upon whether user accepts or rejects the request
                send_admin_update_confirmation_email(hash_key.organization.label, current_admin, new_admin,
                                                     confirm=1 if admin_change_confirmation else None,
                                                     )
                return HttpResponseRedirect('/myaccount/settings/')

    except OrganizationAdminHashKeys.DoesNotExist:
        activation_status = 3

    except UserExtendedProfile.DoesNotExist:
        activation_status = 5

    if activation_status == 5 and admin_activation:
        hash_key.is_hash_consumed = True
        hash_key.save()

        url = reverse('register_user', kwargs={
            'initial_mode': 'register',
            'org_name': base64.b64encode(str(hash_key.organization.label)),
            'admin_email': base64.b64encode(str(hash_key.suggested_admin_email))})

        messages.add_message(request, messages.INFO,
                             _('Please signup here to become admin for %s' % hash_key.organization.label))
        return HttpResponseRedirect(url)

    context['activation_status'] = activation_status

    if admin_activation:
        return render_to_response('onboarding/admin_activation.html', context)

    context['username'] = new_admin.username if new_admin else None

    return render_to_response('onboarding/admin_change_confirmation.html', context)


@csrf_exempt
def get_partner_networks(request, *args, **kwargs):
    """
    Used to fetch the details of partner networks for a organization
    :param request:
    :org_id: organization id
    :opt_in: 0 > False and 1 > True. Decides which partners to filter
    :return:
    [
      {
        "label": "Echidna Giving",
        "code": "ECHIDNA",
        "affiliated_name": "grantee",
        "program_name": "Capacity Building Program",
        "show_opt_in": true
      }
    ]
    """
    opt_in = request.GET.get('opt_in', None)
    show_opt_in = bool(int(opt_in)) if opt_in else None

    org = get_object_or_404(Organization, id=kwargs.get('org_id'))

    query = Q(code__in=org.get_active_partners())
    if opt_in:
        query &= Q(show_opt_in=show_opt_in)

    partner_networks = PartnerNetwork.objects.filter(query)
    serializer = PartnerNetworkSerializer(partner_networks, many=True)
    data = serializer.data

    return JsonResponse(data, safe=False)
