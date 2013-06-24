log = -> console.log.apply console, arguments
plantTimeout = (ms, cb) -> setTimeout cb, ms


class BatchEnrollment
  constructor: (@$container) ->
    log "setting up instructor dashboard subsection - batch enrollment"

    $emails_input = @$container.find("textarea[name='student-emails']'")
    $btn_enroll = @$container.find("input[name='enroll']'")
    $btn_unenroll = @$container.find("input[name='unenroll']'")
    $checkbox_autoenroll = @$container.find("input[name='auto-enroll']'")
    window.autoenroll = $checkbox_autoenroll
    $task_response = @$container.find(".task-response")

    $emails_input.click -> log 'click $emails_input'
    $btn_enroll.click -> log 'click $btn_enroll'
    $btn_unenroll.click -> log 'click $btn_unenroll'

    $btn_enroll.click ->
      send_data =
        action: 'enroll'
        emails: $emails_input.val()
        auto_enroll: $checkbox_autoenroll.is(':checked')
      $.getJSON $btn_enroll.data('endpoint'), send_data, (data) ->
        log 'received response for enroll button', data
        display_response(data)

    $btn_unenroll.click ->
      send_data =
        action: 'unenroll'
        emails: $emails_input.val()
        auto_enroll: $checkbox_autoenroll.is(':checked')
      $.getJSON $btn_unenroll.data('endpoint'), send_data, (data) ->
        log 'received response for unenroll button', data
        display_response(data)

    display_response = (data_from_server) ->
      $task_response.empty()

      response_code_dict = _.extend {}, data_from_server.results
      # response_code_dict e.g. {'code': ['email1', 'email2'], ...}
      message_ordering = [
        'msg_error_enroll'
        'msg_error_unenroll'
        'msg_enrolled'
        'msg_unenrolled'
        'msg_willautoenroll'
        'msg_allowed'
        'msg_disallowed'
        'msg_already_enrolled'
        'msg_notenrolled'
      ]

      msg_to_txt = {
        msg_already_enrolled: "Already enrolled:"
        msg_enrolled:         "Enrolled:"
        msg_error_enroll:     "There was an error enrolling these students:"
        msg_allowed:          "These students will be allowed to enroll once they register:"
        msg_willautoenroll:   "These students will be enrolled once they register:"
        msg_unenrolled:       "Unenrolled:"
        msg_error_unenroll:   "There was an error unenrolling these students:"
        msg_disallowed:       "These students were removed from those who can enroll once they register:"
        msg_notenrolled:      "These students were not enrolled:"
      }

      msg_to_codes = {
        msg_already_enrolled: ['user/ce/alreadyenrolled']
        msg_enrolled:         ['user/!ce/enrolled']
        msg_error_enroll:     ['user/!ce/rejected']
        msg_allowed:          ['!user/cea/allowed', '!user/!cea/allowed']
        msg_willautoenroll:   ['!user/cea/willautoenroll', '!user/!cea/willautoenroll']
        msg_unenrolled:       ['ce/unenrolled']
        msg_error_unenroll:   ['ce/rejected']
        msg_disallowed:       ['cea/disallowed']
        msg_notenrolled:      ['!ce/notenrolled']
      }

      for msg_symbol in message_ordering
        # $task_response.text JSON.stringify(data)
        msg_txt = msg_to_txt[msg_symbol]
        task_res_section = $ '<div/>', class: 'task-res-section'
        task_res_section.append $ '<h3/>', text: msg_txt
        email_list = $ '<ul/>'
        task_res_section.append email_list
        will_attach = false

        for code in msg_to_codes[msg_symbol]
          emails = response_code_dict[code]

          if emails and emails.length
            for email in emails
              email_list.append $ '<li/>', text: email
              will_attach = true

        if will_attach
          $task_response.append task_res_section
        else
          task_res_section.remove()


# manages a list of instructors or staff and the control of their access.
class AuthList
  # rolename is in ['instructor', 'staff'] for instructor_staff endpoints
  # rolename is the name of Role for forums for the forum endpoints
  constructor: (@$container, @rolename) ->
    log "setting up instructor dashboard subsection - authlist management for #{@rolename}"

    @$display_table = @$container.find('.auth-list-table')
    @$add_section   = @$container.find('.auth-list-add')
    $allow_field    = @$add_section.find("input[name='email']")
    $allow_button   = @$add_section.find("input[name='allow']")

    $allow_button.click =>
      @access_change($allow_field.val(), @rolename, 'allow', @reload_auth_list)
      $allow_field.val ''

    @reload_auth_list()

  reload_auth_list: =>
    list_endpoint = @$display_table.data 'endpoint'
    $.getJSON list_endpoint, {rolename: @rolename}, (data) =>

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
          @access_change(item.email, @rolename, 'revoke', @reload_auth_list)

  # slickgrid collapses when rendered in an invisible div
  # use this method to reload the widget
  refresh: ->
    @$display_table.empty()
    @reload_auth_list()

  access_change: (email, rolename, mode, cb) ->
    access_change_endpoint = @$add_section.data 'endpoint'
    $.getJSON access_change_endpoint, {email: email, rolename: @rolename, mode: mode}, (data) ->
      cb?(data)


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
