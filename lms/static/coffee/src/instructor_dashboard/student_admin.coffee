log = -> console.log.apply console, arguments
plantTimeout = (ms, cb) -> setTimeout cb, ms


std_ajax_err = (handler) -> (jqXHR, textStatus, errorThrown) ->
  console.warn """ajax error
                  textStatus: #{textStatus}
                  errorThrown: #{errorThrown}"""
  handler.apply this, arguments


class StudentAdmin
  constructor: (@$container) ->
    log "setting up instructor dashboard section - student admin"

    # get jquery element and assert its existance
    # for debugging
    find_and_assert = ($root, selector) ->
      item = $root.find selector
      if item.length != 1
        console.error "element selection failed for '#{selector}' resulted in length #{item.length}"
        throw "Failed Element Selection"
      else
        item

    # collect buttons
    @$field_student_select        = find_and_assert @$container, "input[name='student-select']"
    @$progress_link               = find_and_assert @$container, "a.progress-link"
    @$btn_enroll                  = find_and_assert @$container, "input[name='enroll']"
    @$btn_unenroll                = find_and_assert @$container, "input[name='unenroll']"
    @$field_problem_select_single = find_and_assert @$container, "input[name='problem-select-single']"
    @$btn_reset_attempts_single   = find_and_assert @$container, "input[name='reset-attempts-single']"
    @$btn_delete_state_single     = find_and_assert @$container, "input[name='delete-state-single']"
    @$btn_rescore_problem_single  = find_and_assert @$container, "input[name='rescore-problem-single']"
    @$btn_task_history_single     = find_and_assert @$container, "input[name='task-history-single']"
    @$field_problem_select_all    = find_and_assert @$container, "input[name='problem-select-all']"
    @$btn_reset_attempts_all      = find_and_assert @$container, "input[name='reset-attempts-all']"
    @$btn_rescore_problem_all     = find_and_assert @$container, "input[name='rescore-problem-all']"
    @$btn_task_history_all        = find_and_assert @$container, "input[name='task-history-all']"


    # go to student progress page
    @$progress_link.click (e) =>
      e.preventDefault()
      email = @$field_student_select.val()

      $.ajax
        dataType: 'json'
        url: @$progress_link.data 'endpoint'
        data: student_email: email
        success: (data) ->
          log 'redirecting...'
          window.location = data.progress_url
        error: std_ajax_err -> console.warn 'error getting student progress url for ' + email

    # enroll student
    @$btn_enroll.click =>
      send_data =
        action: 'enroll'
        emails: @$field_student_select.val()
        auto_enroll: false

      $.ajax
        dataType: 'json'
        url: @$btn_unenroll.data 'endpoint'
        data: send_data
        success: -> console.log "student #{send_data.emails} enrolled"
        error: std_ajax_err -> console.warn 'error enrolling student'

    # unenroll student
    @$btn_unenroll.click =>
      send_data =
        action: 'unenroll'
        emails: @$field_student_select.val()
        auto_enroll: false

      $.ajax
        dataType: 'json'
        url: @$btn_unenroll.data 'endpoint'
        data: send_data
        success: -> console.log "student #{send_data.emails} unenrolled"
        error: std_ajax_err -> console.warn 'error unenrolling student'

    # reset attempts for student on problem
    @$btn_reset_attempts_single.click =>
      send_data =
        student_email: @$field_student_select.val()
        problem_to_reset: @$field_problem_select_single.val()
        delete_module: false

      $.ajax
        dataType: 'json'
        url: @$btn_reset_attempts_single.data 'endpoint'
        data: send_data
        success: -> log 'problem attempts reset'
        error: std_ajax_err   -> console.warn 'error resetting problem state'

    # delete state for student on problem
    @$btn_delete_state_single.click =>
      send_data =
        student_email: @$field_student_select.val()
        problem_to_reset: @$field_problem_select_single.val()
        delete_module: true

      $.ajax
        dataType: 'json'
        url: @$btn_delete_state_single.data 'endpoint'
        data: send_data
        success: -> log 'module state deleted'
        error: std_ajax_err   -> console.warn 'error deleting problem state'

    # start task to rescore problem for student
    @$btn_rescore_problem_single.click =>
      send_data =
        student_email: @$field_student_select.val()
        problem_to_reset: @$field_problem_select_single.val()

      $.ajax
        dataType: 'json'
        url: @$btn_rescore_problem_single.data 'endpoint'
        data: send_data
        success: -> log 'started rescore problem task'
        error: std_ajax_err   -> console.warn 'error starting rescore problem (single student) task'

    # TODO
    # @$btn_task_history_single

    # start task to reset attempts on problem for all students
    @$btn_reset_attempts_all.click =>
      send_data =
        all_students: true
        problem_to_reset: @$field_problem_select_all.val()

      $.ajax
        dataType: 'json'
        url: @$btn_reset_attempts_all.data 'endpoint'
        data: send_data
        success: -> log 'started reset attempts task'
        error: std_ajax_err (jqXHR, textStatus, errorThrown) ->
          console.warn "error starting reset attempts (all students) task"

    # start task to rescore problem for all students
    @$btn_rescore_problem_all.click =>
      send_data =
        all_students: true
        problem_to_reset: @$field_problem_select_all.val()

      $.ajax
        dataType: 'json'
        url: @$btn_rescore_problem_all.data 'endpoint'
        data: send_data
        success: -> log 'started rescore problem task'
        error: std_ajax_err (jqXHR, textStatus, errorThrown) ->
          console.warn "error starting rescore problem (all students) task"

    # TODO
    # @$btn_task_history_all



# exports
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    StudentAdmin: StudentAdmin
