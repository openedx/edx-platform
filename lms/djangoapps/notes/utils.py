def notes_enabled_for_course(course):
    ''' 
    Returns True if the notes app is enabled for the course, False otherwise. 
    '''
    # TODO: create a separate policy setting to enable/disable notes 
    tab_type = 'notes'
    tabs = course.tabs
    tab_found = next((True for t in tabs if t['type'] == tab_type), False)
    return tab_found
