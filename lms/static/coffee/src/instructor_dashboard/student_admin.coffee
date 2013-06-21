log = -> console.log.apply console, arguments
plantTimeout = (ms, cb) -> setTimeout cb, ms


class StudentAdmin
  constructor: (@$section) ->
    log "setting up instructor dashboard section - student admin"

    @$student_email_field = @$section.find("input[name='student-select']")
    @$student_progress_link = @$section.find('a.progress-link')
    @$unenroll_btn = @$section.find("input[name='unenroll']")
    @$problem_select_field = @$section.find("input[name='problem-select']")
    @$reset_attempts_btn = @$section.find("input[name='reset-attempts']")
    @$delete_states_btn = @$section.find("input[name='delete-state']")

    @$student_progress_link.click (e) =>
      e.preventDefault()
      email = @$student_email_field.val()
      @get_student_progress_link email,
        success: (data) ->
          log 'redirecting...'
          window.location = data.progress_url
        error: ->
          console.warn 'error getting student progress url for ' + email

    @$unenroll_btn.click =>
      send_data =
        action: 'unenroll'
        emails: @$student_email_field.val()
        auto_enroll: false
      $.getJSON @$unenroll_btn.data('endpoint'), send_data, (data) ->
        log data

    @$reset_attempts_btn.click =>
      email = @$student_email_field.val()
      problem_to_reset = @$problem_select_field.val()
      @reset_student_progress email, problem_to_reset, false,
        success: -> log 'problem attempts reset!'
        error:   -> console.warn 'error resetting problem state'

    @$delete_states_btn.click =>
      email = @$student_email_field.val()
      problem_to_reset = @$problem_select_field.val()
      @reset_student_progress email, problem_to_reset, true,
        success: -> log 'problem state deleted!'
        error:   -> console.warn 'error deleting problem state'


  # handler can be either a callback for success or a mapping e.g. {success: ->, error: ->, complete: ->}
  get_student_progress_link: (student_email, handler) ->
    settings =
      dataType: 'json'
      url: @$student_progress_link.data 'endpoint'
      data: student_email: student_email

    if typeof handler is 'function'
      _.extend settings, success: handler
    else
      _.extend settings, handler

    $.ajax settings


  # handler can be either a callback for success or a mapping e.g. {success: ->, error: ->, complete: ->}
  reset_student_progress: (student_email, problem_to_reset, delete_module, handler) ->
    settings =
      dataType: 'json'
      url: @$reset_attempts_btn.data 'endpoint'
      data:
        student_email: student_email
        problem_to_reset: problem_to_reset
        delete_module: delete_module

    if typeof handler is 'function'
      _.extend settings, success: handler
    else
      _.extend settings, handler

    $.ajax settings



# exports
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    StudentAdmin: StudentAdmin
