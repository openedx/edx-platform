log = -> console.log.apply console, arguments
plantTimeout = (ms, cb) -> setTimeout cb, ms

std_ajax_err = (handler) -> (jqXHR, textStatus, errorThrown) ->
  console.warn """ajax error
                  textStatus: #{textStatus}
                  errorThrown: #{errorThrown}"""
  handler.apply this, arguments


class BatchEnrollment
  constructor: (@$container) ->
    log "setting up instructor dashboard subsection - batch enrollment"

    $emails_input           = @$container.find("textarea[name='student-emails']'")
    $btn_enroll             = @$container.find("input[name='enroll']'")
    $btn_unenroll           = @$container.find("input[name='unenroll']'")
    $checkbox_autoenroll    = @$container.find("input[name='auto-enroll']'")
    $task_response          = @$container.find(".request-response")
    $request_response_error = @$container.find(".request-response-error")

    $emails_input.click -> log 'click $emails_input'
    $btn_enroll.click -> log 'click $btn_enroll'
    $btn_unenroll.click -> log 'click $btn_unenroll'

    $btn_enroll.click ->
      send_data =
        action: 'enroll'
        emails: $emails_input.val()
        auto_enroll: $checkbox_autoenroll.is(':checked')

      $.ajax
        dataType: 'json'
        url: $btn_enroll.data 'endpoint'
        data: send_data
        success: (data) -> display_response(data)
        error: std_ajax_err -> fail_with_error "Error enrolling/unenrolling students."

    $btn_unenroll.click ->
      send_data =
        action: 'unenroll'
        emails: $emails_input.val()
        auto_enroll: $checkbox_autoenroll.is(':checked')

      $.ajax
        dataType: 'json'
        url: $btn_unenroll.data 'endpoint'
        data: send_data
        success: (data) -> display_response(data)
        error: std_ajax_err -> fail_with_error "Error enrolling/unenrolling students."


    fail_with_error = (msg) ->
      console.warn msg
      $task_response.empty()
      $request_response_error.empty()
      $request_response_error.text msg

    display_response = (data_from_server) ->
      $task_response.empty()
      $request_response_error.empty()

      # these results arrays contain student_results
      # only populated arrays will be rendered
      #
      # students for which there was an error during the action
      errors = []
      # students who are now enrolled in the course
      enrolled = []
      # students who are now allowed to enroll in the course
      allowed = []
      # students who will be autoenrolled on registration
      autoenrolled = []
      # students who are now not enrolled in the course
      notenrolled = []

      # categorize student results into the above arrays.
      for student_results in data_from_server.results
        # for a successful action.
        # student_results is of the form {
        #   "email": "jd405@edx.org",
        #   "before": {
        #     "enrollment": true,
        #     "auto_enroll": false,
        #     "user": true,
        #     "allowed": false
        #   }
        #   "after": {
        #     "enrollment": true,
        #     "auto_enroll": false,
        #     "user": true,
        #     "allowed": false
        #   },
        # }
        #
        # for an action error.
        # student_results is of the form {
        #   'email': email,
        #   'error': True,
        # }

        if student_results.error != undefined
          errors.push student_results
        else if student_results.after.enrollment
          enrolled.push student_results
        else if student_results.after.allowed
          if student_results.after.auto_enroll
            autoenrolled.push student_results
          else
            allowed.push student_results
        else if not student_results.after.enrollment
          notenrolled.push student_results
        else
          console.warn 'student results not reported to user'
          console.warn student_results

      # render populated result arrays
      render_list = (label, emails) ->
        log emails
        task_res_section = $ '<div/>', class: 'request-res-section'
        task_res_section.append $ '<h3/>', text: label
        email_list = $ '<ul/>'
        task_res_section.append email_list

        for email in emails
          email_list.append $ '<li/>', text: email

        $task_response.append task_res_section

      if errors.length
        errors_label = do ->
          if data_from_server.action is 'enroll'
            "There was an error enrolling:"
          else if data_from_server.action is 'unenroll'
            "There was an error unenrolling:"
          else
            console.warn "unknown action from server '#{data_from_server.action}'"
            "There was an error processing:"

        for student_results in errors
          console.log 'error with': student_results.email

      if enrolled.length
        render_list "Students Enrolled:", (sr.email for sr in enrolled)

      if allowed.length
        render_list "These students will be allowed to enroll once they register:",
          (sr.email for sr in allowed)

      if autoenrolled.length
        render_list "These students will be enrolled once they register:",
          (sr.email for sr in autoenrolled)

      if notenrolled.length
        render_list "These students are now not enrolled:",
          (sr.email for sr in notenrolled)


# manages a list of instructors or staff and the control of their access.
class AuthList
  # rolename is in ['instructor', 'staff'] for instructor_staff endpoints
  # rolename is the name of Role for forums for the forum endpoints
  constructor: (@$container, @rolename) ->
    log "setting up instructor dashboard subsection - authlist management for #{@rolename}"

    @$display_table          = @$container.find('.auth-list-table')
    @$request_response_error = @$container.find('.request-response-error')
    @$add_section            = @$container.find('.auth-list-add')
    @$allow_field             = @$add_section.find("input[name='email']")
    @$allow_button            = @$add_section.find("input[name='allow']")

    @$allow_button.click =>
      @access_change @$allow_field.val(), @rolename, 'allow', => @reload_auth_list()
      @$allow_field.val ''

    @reload_auth_list()

  reload_auth_list: ->
    load_auth_list = (data) =>
      @$request_response_error.empty()
      @$display_table.empty()

      options =
        enableCellNavigation: true
        enableColumnReorder: false
        # autoHeight: true
        forceFitColumns: true

      WHICH_CELL_IS_REVOKE = 3
      columns = [
        id: 'username'
        field: 'username'
        name: 'Username'
      ,
        id: 'email'
        field: 'email'
        name: 'Email'
      ,
        id: 'first_name'
        field: 'first_name'
        name: 'First Name'
      ,
      #   id: 'last_name'
      #   field: 'last_name'
      #   name: 'Last Name'
      # ,
        id: 'revoke'
        field: 'revoke'
        name: 'Revoke'
        formatter: (row, cell, value, columnDef, dataContext) ->
          "<span class='revoke-link'>Revoke Access</span>"
      ]

      table_data = data[@rolename]

      $table_placeholder = $ '<div/>', class: 'slickgrid'
      @$display_table.append $table_placeholder
      grid = new Slick.Grid($table_placeholder, table_data, columns, options)
      # grid.autosizeColumns()

      grid.onClick.subscribe (e, args) =>
        item = args.grid.getDataItem(args.row)
        if args.cell is WHICH_CELL_IS_REVOKE
          @access_change item.email, @rolename, 'revoke', => @reload_auth_list()

    $.ajax
      dataType: 'json'
      url: @$display_table.data 'endpoint'
      data: rolename: @rolename
      success: load_auth_list
      error: std_ajax_err => @$request_response_error.text "Error fetching list for '#{@rolename}'"


  # slickgrid collapses when rendered in an invisible div
  # use this method to reload the widget
  refresh: ->
    @$display_table.empty()
    @reload_auth_list()

  access_change: (email, rolename, mode, cb) ->
    $.ajax
      dataType: 'json'
      url: @$add_section.data 'endpoint'
      data:
        email: email
        rolename: rolename
        mode: mode
      success: (data) -> cb?(data)
      error: std_ajax_err => @$request_response_error.text "Error changing user's permissions."


class Membership
  constructor: (@$section) ->
    log "setting up instructor dashboard section - membership"
    @$section.data 'wrapper', @

    @$list_selector = @$section.find('select#member-lists-selector')

    plantTimeout 0, => @batchenrollment = new BatchEnrollment @$section.find '.batch-enrollment'

    @auth_lists = _.map (@$section.find '.auth-list-container'), (auth_list_container) ->
      rolename = $(auth_list_container).data 'rolename'
      new AuthList $(auth_list_container), rolename

    # populate selector
    @$list_selector.empty()
    for auth_list in @auth_lists
      @$list_selector.append $ '<option/>',
        text: auth_list.$container.data 'display-name'
        data:
          auth_list: auth_list

    @$list_selector.change =>
      $opt = @$list_selector.children('option:selected')
      for auth_list in @auth_lists
        auth_list.$container.removeClass 'active'
      auth_list = $opt.data('auth_list')
      auth_list.refresh()
      auth_list.$container.addClass 'active'

    @$list_selector.change()


  onClickTitle: ->
    for auth_list in @auth_lists
      auth_list.refresh()


# exports
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    Membership: Membership
