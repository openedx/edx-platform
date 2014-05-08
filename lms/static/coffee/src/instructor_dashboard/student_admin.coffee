###
Student Admin Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

# Load utilities
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments
create_task_list_table = -> window.InstructorDashboard.util.create_task_list_table.apply this, arguments
PendingInstructorTasks = -> window.InstructorDashboard.util.PendingInstructorTasks


# get jquery element and assert its existance
find_and_assert = ($root, selector) ->
  item = $root.find selector
  if item.length != 1
    console.error "element selection failed for '#{selector}' resulted in length #{item.length}"
    throw "Failed Element Selection"
  else
    item


class StudentAdmin
  constructor: (@$section) ->
    # attach self to html so that instructor_dashboard.coffee can find
    #  this object to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @

    # gather buttons
    # some buttons are optional because they can be flipped by the instructor task feature switch
    # student-specific
    @$field_student_select_progress = find_and_assert @$section, "input[name='student-select-progress']"
    @$field_student_select_grade  = find_and_assert @$section, "input[name='student-select-grade']"
    @$progress_link               = find_and_assert @$section, "a.progress-link"
    @$field_problem_select_single = find_and_assert @$section, "input[name='problem-select-single']"
    @$btn_reset_attempts_single   = find_and_assert @$section, "input[name='reset-attempts-single']"
    @$btn_delete_state_single     = @$section.find "input[name='delete-state-single']"
    @$btn_rescore_problem_single  = @$section.find "input[name='rescore-problem-single']"
    @$btn_task_history_single     = @$section.find "input[name='task-history-single']"
    @$table_task_history_single   = @$section.find ".task-history-single-table"

    # course-specific
    @$field_problem_select_all    = @$section.find "input[name='problem-select-all']"
    @$btn_reset_attempts_all      = @$section.find "input[name='reset-attempts-all']"
    @$btn_rescore_problem_all     = @$section.find "input[name='rescore-problem-all']"
    @$btn_task_history_all        = @$section.find "input[name='task-history-all']"
    @$table_task_history_all      = @$section.find ".task-history-all-table"
    @instructor_tasks             = new (PendingInstructorTasks()) @$section

    # response areas
    @$request_response_error_progress = find_and_assert @$section, ".student-specific-container .request-response-error"
    @$request_response_error_grade = find_and_assert @$section, ".student-grade-container .request-response-error"
    @$request_response_error_all    = @$section.find ".course-specific-container .request-response-error"

    # attach click handlers

    # go to student progress page
    @$progress_link.click (e) =>
      e.preventDefault()
      unique_student_identifier = @$field_student_select_progress.val()
      if not unique_student_identifier
        return @$request_response_error_progress.text gettext("Please enter a student email address or username.")
      error_message = gettext("Error getting student progress url for '<%= student_id %>'. Check that the student identifier is spelled correctly.")
      full_error_message = _.template(error_message, {student_id: unique_student_identifier})

      $.ajax
        dataType: 'json'
        url: @$progress_link.data 'endpoint'
        data: unique_student_identifier: unique_student_identifier
        success: @clear_errors_then (data) ->
          window.location = data.progress_url
        error: std_ajax_err => @$request_response_error_progress.text full_error_message

    # reset attempts for student on problem
    @$btn_reset_attempts_single.click =>
      unique_student_identifier = @$field_student_select_grade.val()
      problem_to_reset = @$field_problem_select_single.val()
      if not unique_student_identifier
        return @$request_response_error_grade.text gettext("Please enter a student email address or username.")
      if not problem_to_reset
        return @$request_response_error_grade.text gettext("Please enter a problem location.")
      send_data =
        unique_student_identifier: unique_student_identifier
        problem_to_reset: problem_to_reset
        delete_module: false
      success_message = gettext("Success! Problem attempts reset for problem '<%= problem_id %>' and student '<%= student_id %>'.")
      error_message = gettext("Error resetting problem attempts for problem '<%= problem_id %>' and student '<%= student_id %>'. Check that the problem and student identifiers are spelled correctly.")
      full_success_message = _.template(success_message, {problem_id: problem_to_reset, student_id: unique_student_identifier})
      full_error_message = _.template(error_message, {problem_id: problem_to_reset, student_id: unique_student_identifier})

      $.ajax
        dataType: 'json'
        url: @$btn_reset_attempts_single.data 'endpoint'
        data: send_data
        success: @clear_errors_then -> alert full_success_message
        error: std_ajax_err => @$request_response_error_grade.text full_error_message

    # delete state for student on problem
    @$btn_delete_state_single.click =>
      unique_student_identifier = @$field_student_select_grade.val()
      problem_to_reset = @$field_problem_select_single.val()
      if not unique_student_identifier
        return @$request_response_error_grade.text gettext("Please enter a student email address or username.")
      if not problem_to_reset
        return @$request_response_error_grade.text gettext("Please enter a problem location.")
      confirm_message = gettext("Delete student '<%= student_id %>'s state on problem '<%= problem_id %>'?")
      full_confirm_message = _.template(confirm_message, {student_id: unique_student_identifier, problem_id: problem_to_reset})

      if window.confirm full_confirm_message
        send_data =
          unique_student_identifier: unique_student_identifier
          problem_to_reset: problem_to_reset
          delete_module: true
        error_message = gettext("Error deleting student '<%= student_id %>'s state on problem '<%= problem_id %>'. Check that the problem and student identifiers are spelled correctly.")
        full_error_message = _.template(error_message, {student_id: unique_student_identifier, problem_id: problem_to_reset})

        $.ajax
          dataType: 'json'
          url: @$btn_delete_state_single.data 'endpoint'
          data: send_data
          success: @clear_errors_then -> alert gettext('Module state successfully deleted.')
          error: std_ajax_err => @$request_response_error_grade.text full_error_message
      else
        # Clear error messages if "Cancel" was chosen on confirmation alert
        @clear_errors()

    # start task to rescore problem for student
    @$btn_rescore_problem_single.click =>
      unique_student_identifier = @$field_student_select_grade.val()
      problem_to_reset = @$field_problem_select_single.val()
      if not unique_student_identifier
        return @$request_response_error_grade.text gettext("Please enter a student email address or username.")
      if not problem_to_reset
        return @$request_response_error_grade.text gettext("Please enter a problem location.")
      send_data =
        unique_student_identifier: unique_student_identifier
        problem_to_reset: problem_to_reset
      success_message = gettext("Started rescore problem task for problem '<%= problem_id %>' and student '<%= student_id %>'. Click the 'Show Background Task History for Student' button to see the status of the task.")
      full_success_message = _.template(success_message, {student_id: unique_student_identifier, problem_id: problem_to_reset})
      error_message = gettext("Error starting a task to rescore problem '<%= problem_id %>' for student '<%= student_id %>'. Check that the problem and student identifiers are spelled correctly.")
      full_error_message = _.template(error_message, {student_id: unique_student_identifier, problem_id: problem_to_reset})

      $.ajax
        dataType: 'json'
        url: @$btn_rescore_problem_single.data 'endpoint'
        data: send_data
        success: @clear_errors_then -> alert full_success_message
        error: std_ajax_err => @$request_response_error_grade.text full_error_message

    # list task history for student+problem
    @$btn_task_history_single.click =>
      unique_student_identifier = @$field_student_select_grade.val()
      problem_to_reset = @$field_problem_select_single.val()
      if not unique_student_identifier
        return @$request_response_error_grade.text gettext("Please enter a student email address or username.")
      if not problem_to_reset
        return @$request_response_error_grade.text gettext("Please enter a problem location.")
      send_data =
        unique_student_identifier: unique_student_identifier
        problem_location_str: problem_to_reset
      error_message = gettext("Error getting task history for problem '<%= problem_id %>' and student '<%= student_id %>'. Check that the problem and student identifiers are spelled correctly.")
      full_error_message = _.template(error_message, {student_id: unique_student_identifier, problem_id: problem_to_reset})

      $.ajax
        dataType: 'json'
        url: @$btn_task_history_single.data 'endpoint'
        data: send_data
        success: @clear_errors_then (data) =>
          create_task_list_table @$table_task_history_single, data.tasks
        error: std_ajax_err => @$request_response_error_grade.text full_error_message

    # start task to reset attempts on problem for all students
    @$btn_reset_attempts_all.click =>
      problem_to_reset = @$field_problem_select_all.val()
      if not problem_to_reset
        return @$request_response_error_all.text gettext("Please enter a problem location.")
      confirm_message = gettext("Reset attempts for all students on problem '<%= problem_id %>'?")
      full_confirm_message = _.template(confirm_message, {problem_id: problem_to_reset})
      if window.confirm full_confirm_message
        send_data =
          all_students: true
          problem_to_reset: problem_to_reset
        success_message = gettext("Successfully started task to reset attempts for problem '<%= problem_id %>'. Click the 'Show Background Task History for Problem' button to see the status of the task.")
        full_success_message = _.template(success_message, {problem_id: problem_to_reset})
        error_message = gettext("Error starting a task to reset attempts for all students on problem '<%= problem_id %>'. Check that the problem identifier is spelled correctly.")
        full_error_message = _.template(error_message, {problem_id: problem_to_reset})

        $.ajax
          dataType: 'json'
          url: @$btn_reset_attempts_all.data 'endpoint'
          data: send_data
          success: @clear_errors_then -> alert full_success_message
          error: std_ajax_err => @$request_response_error_all.text full_error_message
      else
        # Clear error messages if "Cancel" was chosen on confirmation alert
        @clear_errors()

    # start task to rescore problem for all students
    @$btn_rescore_problem_all.click =>
      problem_to_reset = @$field_problem_select_all.val()
      if not problem_to_reset
        return @$request_response_error_all.text gettext("Please enter a problem location.")
      confirm_message = gettext("Rescore problem '<%= problem_id %>' for all students?")
      full_confirm_message = _.template(confirm_message, {problem_id: problem_to_reset})
      if window.confirm full_confirm_message
        send_data =
          all_students: true
          problem_to_reset: problem_to_reset
        success_message = gettext("Successfully started task to rescore problem '<%= problem_id %>' for all students. Click the 'Show Background Task History for Problem' button to see the status of the task.")
        full_success_message = _.template(success_message, {problem_id: problem_to_reset})
        error_message = gettext("Error starting a task to rescore problem '<%= problem_id %>'. Check that the problem identifier is spelled correctly.")
        full_error_message = _.template(error_message, {problem_id: problem_to_reset})

        $.ajax
          dataType: 'json'
          url: @$btn_rescore_problem_all.data 'endpoint'
          data: send_data
          success: @clear_errors_then -> alert full_success_message
          error: std_ajax_err => @$request_response_error_all.text full_error_message
      else
        # Clear error messages if "Cancel" was chosen on confirmation alert
        @clear_errors()

    # list task history for problem
    @$btn_task_history_all.click =>
      send_data =
        problem_location_str: @$field_problem_select_all.val()

      if not send_data.problem_location_str
        return @$request_response_error_all.text gettext("Please enter a problem location.")

      $.ajax
        dataType: 'json'
        url: @$btn_task_history_all.data 'endpoint'
        data: send_data
        success: @clear_errors_then (data) =>
          create_task_list_table @$table_task_history_all, data.tasks
        error: std_ajax_err => @$request_response_error_all.text gettext("Error listing task history for this student and problem.")

  # wraps a function, but first clear the error displays
  clear_errors_then: (cb) ->
    @$request_response_error_progress.empty()
    @$request_response_error_grade.empty()
    @$request_response_error_all.empty()
    ->
      cb?.apply this, arguments


  clear_errors: ->
    @$request_response_error_progress.empty()
    @$request_response_error_grade.empty()
    @$request_response_error_all.empty()

  # handler for when the section title is clicked.
  onClickTitle: -> @instructor_tasks.task_poller.start()

  # handler for when the section is closed
  onExit: -> @instructor_tasks.task_poller.stop()


# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  StudentAdmin: StudentAdmin
