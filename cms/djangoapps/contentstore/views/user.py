from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie

from util.json_request import expect_json
from mitxmako.shortcuts import render_to_response

def user_author_string(user):
    '''Get an author string for commits by this user.  Format:
    first last <email@email.com>.

    If the first and last names are blank, uses the username instead.
    Assumes that the email is not blank.
    '''
    f = user.first_name
    l = user.last_name
    if f == '' and l == '':
        f = user.username
    return '{first} {last} <{email}>'.format(first=f,
                                             last=l,
                                             email=user.email)


@login_required
@ensure_csrf_cookie
def manage_users(request, location):
    '''
    This view will return all CMS users who are editors for the specified course
    '''
    # check that logged in user has permissions to this item
    if not has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME) and not has_access(request.user, location, role=STAFF_ROLE_NAME):
        raise PermissionDenied()

    course_module = modulestore().get_item(location)

    return render_to_response('manage_users.html', {
        'active_tab': 'users',
        'context_course': course_module,
        'staff': get_users_in_course_group_by_role(location, STAFF_ROLE_NAME),
        'add_user_postback_url': reverse('add_user', args=[location]).rstrip('/'),
        'remove_user_postback_url': reverse('remove_user', args=[location]).rstrip('/'),
        'allow_actions': has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME),
        'request_user_id': request.user.id
    })




@expect_json
@login_required
@ensure_csrf_cookie
def add_user(request, location):
    '''
    This POST-back view will add a user - specified by email - to the list of editors for
    the specified course
    '''
    email = request.POST["email"]

    if email == '':
        return create_json_response('Please specify an email address.')

    # check that logged in user has admin permissions to this course
    if not has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME):
        raise PermissionDenied()

    user = get_user_by_email(email)

    # user doesn't exist?!? Return error.
    if user is None:
        return create_json_response('Could not find user by email address \'{0}\'.'.format(email))

    # user exists, but hasn't activated account?!?
    if not user.is_active:
        return create_json_response('User {0} has registered but has not yet activated his/her account.'.format(email))

    # ok, we're cool to add to the course group
    add_user_to_course_group(request.user, user, location, STAFF_ROLE_NAME)

    return create_json_response()


@expect_json
@login_required
@ensure_csrf_cookie
def remove_user(request, location):
    '''
    This POST-back view will remove a user - specified by email - from the list of editors for
    the specified course
    '''

    email = request.POST["email"]

    # check that logged in user has admin permissions on this course
    if not has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME):
        raise PermissionDenied()

    user = get_user_by_email(email)
    if user is None:
        return create_json_response('Could not find user by email address \'{0}\'.'.format(email))

    # make sure we're not removing ourselves
    if user.id == request.user.id:
        raise PermissionDenied()

    remove_user_from_course_group(request.user, user, location, STAFF_ROLE_NAME)

    return create_json_response()

