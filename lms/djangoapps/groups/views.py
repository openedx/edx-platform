def groups(request, course_id):
    """Display the join/create/view groups view."""

    course = get_course_by_id(course_id, depth=None)

    context = {
        'course': course,
    }

    return render_to_response('groups/groups.html', context)
