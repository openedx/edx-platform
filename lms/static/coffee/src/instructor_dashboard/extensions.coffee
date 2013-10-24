###
Extensions Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments

# Extensions Section
class Extensions

  constructor: (@$section) ->
    # attach self to html
    # so that instructor_dashboard.coffee can find this object
    # to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @

    # Gather inputs
    @$student_input = @$section.find("input[name='student']")
    @$url_input = @$section.find("select[name='url']")
    @$due_datetime_input = @$section.find("input[name='due_datetime']")

    # Gather buttons
    @$change_due_date = @$section.find("input[name='change-due-date']")
    @$reset_due_date = @$section.find("input[name='reset-due-date']")
    @$show_unit_extensions = @$section.find("input[name='show-unit-extensions']")
    @$show_student_extensions = @$section.find("input[name='show-student-extensions']")

    # Gather notification areas
    @$task_response = @$section.find(".request-response")
    @$task_error = @$section.find(".request-response-error")
    @$task_response.hide()
    @$task_error.hide()

    # Click handlers
    @$change_due_date.click =>
      send_data =
        student: @$student_input.val()
        url: @$url_input.val()
        due_datetime: @$due_datetime_input.val()

      $.ajax
        dataType: 'json'
        url: @$change_due_date.data 'endpoint'
        data: send_data
        success: (data) => @display_response data
        error: (xhr) => @fail_with_error "Error changing due date", xhr
        
  # handler for when the section title is clicked.
  onClickTitle: ->

  fail_with_error: (msg, xhr) ->
    data = $.parseJSON xhr.responseText
    msg += ": " + data['error']
    console.warn msg
    @$task_response.empty()
    @$task_error.empty()
    @$task_error.text msg
    @$task_error.show()

  display_response: (data_from_server) ->
    @$task_error.empty().hide()
    @$task_response.empty().text data_from_server
    @$task_response.show()


# export for use
# create parent namespaces if they do not already exist.
# abort if underscore can not be found.
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    Extensions: Extensions
