# Instructor Dashboard Tab Manager

log = -> console.log.apply console, arguments
plantTimeout = (ms, cb) -> setTimeout cb, ms


CSS_INSTRUCTOR_CONTENT = 'instructor-dashboard-content-2'
CSS_ACTIVE_SECTION = 'active-section'
CSS_IDASH_SECTION = 'idash-section'
CSS_INSTRUCTOR_NAV = 'instructor-nav'

HASH_LINK_PREFIX = '#view-'


# once we're ready, check if this page has the instructor dashboard
$ =>
  instructor_dashboard_content = $ ".#{CSS_INSTRUCTOR_CONTENT}"
  if instructor_dashboard_content.length != 0
    log "setting up instructor dashboard"
    setup_instructor_dashboard          instructor_dashboard_content
    setup_instructor_dashboard_sections instructor_dashboard_content


# enable links
setup_instructor_dashboard = (idash_content) =>
  links = idash_content.find(".#{CSS_INSTRUCTOR_NAV}").find('a')
  # setup section header click handlers
  for link in ($ link for link in links)
    link.click (e) ->
      # deactivate (styling) all sections
      idash_content.find(".#{CSS_IDASH_SECTION}").removeClass CSS_ACTIVE_SECTION
      idash_content.find(".#{CSS_INSTRUCTOR_NAV}").children().removeClass CSS_ACTIVE_SECTION

      # find paired section
      section_name = $(this).data 'section'
      section = idash_content.find "##{section_name}"

      # activate (styling) active
      section.addClass CSS_ACTIVE_SECTION
      $(this).addClass CSS_ACTIVE_SECTION

      # write deep link
      location.hash = "#{HASH_LINK_PREFIX}#{section_name}"

      log "clicked #{section_name}"
      e.preventDefault()

  # recover deep link from url
  # click default or go to section specified by hash
  if (new RegExp "^#{HASH_LINK_PREFIX}").test location.hash
    rmatch = (new RegExp "^#{HASH_LINK_PREFIX}(.*)").exec location.hash
    section_name = rmatch[1]
    link = links.filter "[data-section='#{section_name}']"
    link.click()
  else
    links.eq(0).click()


# call setup handlers for each section
setup_instructor_dashboard_sections = (idash_content) ->
  log "setting up instructor dashboard sections"
  # fault isolation
  # an error thrown in one section will not block other sections from exectuing
  plantTimeout 0, -> new window.InstructorDashboard.sections.DataDownload idash_content.find(".#{CSS_IDASH_SECTION}#data_download")
  plantTimeout 0, -> setup_section_membership    idash_content.find(".#{CSS_IDASH_SECTION}#membership")
  plantTimeout 0, -> new window.InstructorDashboard.sections.Analytics idash_content.find(".#{CSS_IDASH_SECTION}#analytics")


# setup the data download section
setup_section_membership = (section) ->
  log "setting up instructor dashboard section - membership"

  setup_batch_enrollment = ->
    log "setting up instructor dashboard subsection - batch enrollment"

    subsection = section.find('.batch-enrollment')
    emails_input = subsection.find("textarea[name='student-emails']'")
    btn_enroll = subsection.find("input[name='enroll']'")
    btn_unenroll = subsection.find("input[name='unenroll']'")
    task_response = subsection.find(".task-response")

    emails_input.click -> log 'click emails_input'
    btn_enroll.click -> log 'click btn_enroll'
    btn_unenroll.click -> log 'click btn_unenroll'

    btn_enroll.click -> $.getJSON btn_enroll.data('endpoint'), enroll: emails_input.val() , (data) ->
      log 'received response for enroll button', data
      display_response(data)

    btn_unenroll.click -> $.getJSON btn_unenroll.data('endpoint'), unenroll: emails_input.val() , (data) ->
      log 'received response for unenroll button', data
      display_response(data)

    display_response = (data_from_server) ->
      task_response.empty()

      response_code_dict = _.extend {}, data_from_server.enrolled, data_from_server.unenrolled
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
        # task_response.text JSON.stringify(data)
        msg_txt = msg_to_txt[msg_symbol]
        task_res_section = $ '<div/>', class: 'task-res-section'
        task_res_section.append $ '<h3/>', text: msg_txt
        email_list = $ '<ul/>'
        task_res_section.append email_list
        will_attach = false

        for code in msg_to_codes[msg_symbol]
          log 'logging code', code
          emails = response_code_dict[code]
          log 'emails', emails

          if emails and emails.length
            for email in emails
              log 'logging email', email
              email_list.append $ '<li/>', text: email
              will_attach = true

        if will_attach
          task_response.append task_res_section
        else
          task_res_section.remove()


  setup_instructor_staff_management = ->
    log 'setting up instructor dashboard subsection - instructor staff management'

    subsection = section.find('.instructor_staff_management')
    display_table = subsection.find('.staff-management-table')
    add_section = subsection.find('.add-staff')
    allow_field = add_section.find("input[name='staff-email']")
    allow_button = add_section.find("input[name='staff-allow']")
    list_endpoint = display_table.data 'endpoint'
    access_change_endpoint = add_section.data 'endpoint'

    reload_staff_list = ->
      $.getJSON list_endpoint, (data) ->
        log data

        display_table.empty()

        options =
          enableCellNavigation: true
          enableColumnReorder: false

        columns = [
          id: 'username'
          field: 'username'
          name: 'Username'
        ,
          id: 'email'
          field: 'email'
          name: 'Email'
        ,
          id: 'revoke'
          field: 'revoke'
          name: 'Revoke'
          formatter: (row, cell, value, columnDef, dataContext) ->
            "<span class='revoke-link'>Revoke Access</span>"
        ]

        table_data = data.staff
        log 'table_data', table_data

        table_placeholder = $ '<div/>', class: 'slickgrid'
        display_table.append table_placeholder
        log 'display_table', table_placeholder
        grid = new Slick.Grid(table_placeholder, table_data, columns, options)
        grid.autosizeColumns()

        grid.onClick.subscribe (e, args) ->
          item = args.grid.getDataItem(args.row)
          if args.cell is 2
            access_change(item.email, 'staff', 'revoke', reload_staff_list)

    allow_button.click ->
      access_change(allow_field.val(), 'staff', 'allow', reload_staff_list)
      allow_field.val ''

    access_change = (email, level, mode, cb) ->
      url = access_change_endpoint
      $.getJSON access_change_endpoint, {email: email, level: level, mode: mode}, (data) ->
        log data
        cb?()

    reload_staff_list()


  setup_batch_enrollment()
  setup_instructor_staff_management()
