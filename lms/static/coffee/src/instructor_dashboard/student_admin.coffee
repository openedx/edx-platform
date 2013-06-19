log = -> console.log.apply console, arguments
plantTimeout = (ms, cb) -> setTimeout cb, ms


class StudentAdmin
  constructor: (@$section) ->
    log "setting up instructor dashboard section - student admin"

    @$student_email = @$section.find("input[name='student-select']")
    @$student_progress_link = @$section.find('a.progress-link')
    @$unenroll_btn = @$section.find("input[name='unenroll']")

    @$student_progress_link.click (e) =>
      e.preventDefault()
      email = @$student_email.val()
      @get_student_progress_link email,
        success: (data) ->
          log 'redirecting'
          window.location = data.progress_url
        error: ->
          console.warn 'error getting student progress url for ' + email

    @$unenroll_btn.click =>
      log 'VAL', @$student_email.val()
      $.getJSON @$unenroll_btn.data('endpoint'), unenroll: @$student_email.val(), (data) ->
        log 'data'

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



# exports
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  StudentAdmin: StudentAdmin
