log = -> console.log.apply console, arguments
plantTimeout = (ms, cb) -> setTimeout cb, ms
plantInterval = (ms, cb) -> setInterval cb, ms


std_ajax_err = (handler) -> (jqXHR, textStatus, errorThrown) ->
  console.warn """ajax error
                  textStatus: #{textStatus}
                  errorThrown: #{errorThrown}"""
  handler.apply this, arguments


create_task_list_table = ($table_tasks, tasks_data) ->
  $table_tasks.empty()

  options =
    enableCellNavigation: true
    enableColumnReorder: false
    autoHeight: true
    rowHeight: 60
    forceFitColumns: true

  columns = [
    id: 'task_type'
    field: 'task_type'
    name: 'Task Type'
  ,
    id: 'requester'
    field: 'requester'
    name: 'Requester'
    width: 30
  ,
    id: 'task_input'
    field: 'task_input'
    name: 'Input'
  ,
    id: 'task_state'
    field: 'task_state'
    name: 'State'
    width: 30
  ,
    id: 'task_id'
    field: 'task_id'
    name: 'Task ID'
    width: 50
  ,
    id: 'created'
    field: 'created'
    name: 'Created'
  ]

  table_data = tasks_data

  $table_placeholder = $ '<div/>', class: 'slickgrid'
  $table_tasks.append $table_placeholder
  grid = new Slick.Grid($table_placeholder, table_data, columns, options)


class StudentAdmin
  constructor: (@$section) ->
    log "setting up instructor dashboard section - student admin"
    @$section.data 'wrapper', @

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
    @$field_student_select        = find_and_assert @$section, "input[name='student-select']"
    @$progress_link               = find_and_assert @$section, "a.progress-link"
    @$btn_enroll                  = find_and_assert @$section, "input[name='enroll']"
    @$btn_unenroll                = find_and_assert @$section, "input[name='unenroll']"
    @$field_problem_select_single = find_and_assert @$section, "input[name='problem-select-single']"
    @$btn_reset_attempts_single   = find_and_assert @$section, "input[name='reset-attempts-single']"
    @$btn_delete_state_single     = find_and_assert @$section, "input[name='delete-state-single']"
    @$btn_rescore_problem_single  = find_and_assert @$section, "input[name='rescore-problem-single']"
    @$btn_task_history_single     = find_and_assert @$section, "input[name='task-history-single']"
    @$table_task_history_single   = find_and_assert @$section, ".task-history-single-table"

    @$field_problem_select_all    = find_and_assert @$section, "input[name='problem-select-all']"
    @$btn_reset_attempts_all      = find_and_assert @$section, "input[name='reset-attempts-all']"
    @$btn_rescore_problem_all     = find_and_assert @$section, "input[name='rescore-problem-all']"
    @$btn_task_history_all        = find_and_assert @$section, "input[name='task-history-all']"
    @$table_task_history_all      = find_and_assert @$section, ".task-history-all-table"
    @$table_running_tasks         = find_and_assert @$section, ".running-tasks-table"

    @$request_response_error_single = find_and_assert @$section, ".student-specific-container .request-response-error"
    @$request_response_error_all    = find_and_assert @$section, ".course-specific-container .request-response-error"

    @start_refresh_running_task_poll_loop()

    # go to student progress page
    @$progress_link.click (e) =>
      e.preventDefault()
      email = @$field_student_select.val()

      $.ajax
        dataType: 'json'
        url: @$progress_link.data 'endpoint'
        data: student_email: email
        success: @clear_errors_then (data) ->
          log 'redirecting...'
          window.location = data.progress_url
        error: std_ajax_err => @$request_response_error_single.text "Error getting student progress url for '#{email}'."

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
        success: @clear_errors_then -> console.log "student #{send_data.emails} enrolled"
        error: std_ajax_err => @$request_response_error_single.text "Error enrolling student '#{send_data.emails}'."

    # unenroll student
    @$btn_unenroll.click =>
      send_data =
        action: 'unenroll'
        emails: @$field_student_select.val()

      $.ajax
        dataType: 'json'
        url: @$btn_unenroll.data 'endpoint'
        data: send_data
        success: @clear_errors_then -> console.log "student #{send_data.emails} unenrolled"
        error: std_ajax_err => @$request_response_error_single.text "Error unenrolling student '#{send_data.emails}'."

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
        success: @clear_errors_then -> log 'problem attempts reset'
        error: std_ajax_err => @$request_response_error_single.text "Error resetting problem attempts."

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
        success: @clear_errors_then -> log 'module state deleted'
        error: std_ajax_err => @$request_response_error_single.text "Error deleting problem state."

    # start task to rescore problem for student
    @$btn_rescore_problem_single.click =>
      send_data =
        student_email: @$field_student_select.val()
        problem_to_reset: @$field_problem_select_single.val()

      $.ajax
        dataType: 'json'
        url: @$btn_rescore_problem_single.data 'endpoint'
        data: send_data
        success: @clear_errors_then -> log 'started rescore problem task'
        error: std_ajax_err => @$request_response_error_single.text "Error starting a task to rescore student's problem."

    # list task history for student+problem
    @$btn_task_history_single.click =>
      send_data =
        student_email: @$field_student_select.val()
        problem_urlname: @$field_problem_select_single.val()

      if not send_data.student_email
        return @$request_response_error_single.text "Enter a student email."
      if not send_data.problem_urlname
        return @$request_response_error_single.text "Enter a problem urlname."

      $.ajax
        dataType: 'json'
        url: @$btn_task_history_single.data 'endpoint'
        data: send_data
        success: @clear_errors_then (data) =>
          create_task_list_table @$table_task_history_single, data.tasks
        error: std_ajax_err => @$request_response_error_single.text "Error getting task history for student+problem"

    # start task to reset attempts on problem for all students
    @$btn_reset_attempts_all.click =>
      send_data =
        all_students: true
        problem_to_reset: @$field_problem_select_all.val()

      $.ajax
        dataType: 'json'
        url: @$btn_reset_attempts_all.data 'endpoint'
        data: send_data
        success: @clear_errors_then -> log 'started reset attempts task'
        error: std_ajax_err => @$request_response_error_all.text "Error starting a task to reset attempts for all students on this problem."

    # start task to rescore problem for all students
    @$btn_rescore_problem_all.click =>
      send_data =
        all_students: true
        problem_to_reset: @$field_problem_select_all.val()

      $.ajax
        dataType: 'json'
        url: @$btn_rescore_problem_all.data 'endpoint'
        data: send_data
        success: @clear_errors_then -> log 'started rescore problem task'
        error: std_ajax_err => @$request_response_error_all.text "Error starting a task to rescore this problem for all students."

    # list task history for problem
    @$btn_task_history_all.click =>
      send_data =
        problem_urlname: @$field_problem_select_all.val()

      if not send_data.problem_urlname
        return @$request_response_error_all.text "Enter a problem urlname."

      $.ajax
        dataType: 'json'
        url: @$btn_task_history_all.data 'endpoint'
        data: send_data
        success: @clear_errors_then (data) =>
          create_task_list_table @$table_task_history_all, data.tasks
        error: std_ajax_err => @$request_response_error_all.text "Error listing task history for this student and problem."


  reload_running_tasks_list: =>
    list_endpoint = @$table_running_tasks.data 'endpoint'
    $.ajax
      dataType: 'json'
      url: list_endpoint
      success: (data) => create_task_list_table @$table_running_tasks, data.tasks
      error: std_ajax_err => console.warn "error listing all instructor tasks"

  start_refresh_running_task_poll_loop: ->
    @reload_running_tasks_list()
    if @$section.hasClass 'active-section'
      plantTimeout 5000, => @start_refresh_running_task_poll_loop()

  clear_errors_then: (cb) ->
    @$request_response_error_single.empty()
    @$request_response_error_all.empty()
    ->
      cb?.apply this, arguments

  onClickTitle: ->
    @start_refresh_running_task_poll_loop()

  # onExit: ->
  #   clearInterval @reload_running_task_list_slot


# exports
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    StudentAdmin: StudentAdmin
