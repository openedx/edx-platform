# TODO: make a separate policy setting to enable/disable notes. 
def notes_enabled_for_course(course):
    ''' Returns True if notes are enabled for the course, False otherwise. '''
    notes_tab_type = 'notes'
    return next((True for tab in course.tabs if tab['type'] == notes_tab_type), False)
