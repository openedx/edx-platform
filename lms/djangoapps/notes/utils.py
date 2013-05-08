def notes_enabled_for_course(course):
    ''' 
    Returns True if the notes app is enabled for the course, False otherwise. 
    '''
    # TODO: create a separate policy setting to enable/disable notes 
    notes_tab_type = 'notes'
    return next((True for tab in course.tabs if tab['type'] == notes_tab_type), False)
