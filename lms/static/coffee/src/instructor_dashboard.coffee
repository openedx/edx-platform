# Instructor Dashboard Tab Manager

log = -> console.log.apply console, arguments

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
  setup_section_enrollment    idash_content.find(".#{CSS_IDASH_SECTION}#enrollment")
  setup_section_data_download idash_content.find(".#{CSS_IDASH_SECTION}#data_download")
  setup_section_analytics     idash_content.find(".#{CSS_IDASH_SECTION}#analytics")


# setup the data download section
setup_section_enrollment = (section) ->
  log "setting up instructor dashboard section - enrollment"

  emails_input = section.find("textarea[name='student-emails']'")
  btn_enroll = section.find("input[name='enroll']'")
  btn_unenroll = section.find("input[name='unenroll']'")
  task_response = section.find(".task-response")

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


# setup the data download section
setup_section_data_download = (section) ->
  log "setting up instructor dashboard section - data download"

  display = section.find('.data-display')
  display_text = display.find('.data-display-text')
  display_table = display.find('.data-display-table')

  reset_display = ->
    display_text.empty()
    display_table.empty()

  list_studs_btn = section.find("input[name='list-profiles']'")
  list_studs_btn.click (e) ->
    log "fetching student list"
    url = $(this).data('endpoint')
    if $(this).data 'csv'
      url += '/csv'
      location.href = url
    else
      reset_display()
      $.getJSON url, (data) ->
        # setup SlickGrid
        options =
          enableCellNavigation: true
          enableColumnReorder: false

        columns = ({id: feature, field: feature, name: feature} for feature in data.queried_features)
        grid_data = data.students

        table_placeholder = $ '<div/>', class: 'slickgrid'
        display_table.append table_placeholder
        grid = new Slick.Grid(table_placeholder, grid_data, columns, options)
        grid.autosizeColumns()


  grade_config_btn = section.find("input[name='dump-gradeconf']'")
  grade_config_btn.click (e) ->
    log "fetching grading config"
    url = $(this).data('endpoint')
    $.getJSON url, (data) ->
      reset_display()
      display_text.html data['grading_config_summary']


# setup the analytics section
setup_section_analytics = (section) ->
  log "setting up instructor dashboard section - analytics"

  display = section.find('.distribution-display')
  display_text = display.find('.distribution-display-text')
  display_graph = display.find('.distribution-display-graph')
  display_table = display.find('.distribution-display-table')

  reset_display = ->
    display_text.empty()
    display_graph.empty()
    display_table.empty()

  distribution_select = section.find('select#distributions')

  # ask for available distributions
  $.getJSON distribution_select.data('endpoint'), features: JSON.stringify([]), (data) ->
      distribution_select.find('option').eq(0).text "-- Select distribution"

      for feature in data.available_features
        opt = $ '<option/>',
          text: data.display_names[feature]
          data:
            feature: feature

        distribution_select.append opt

      distribution_select.change ->
        opt = $(this).children('option:selected')
        log "distribution selected: #{opt.data 'feature'}"
        feature = opt.data 'feature'
        reset_display()
        $.getJSON distribution_select.data('endpoint'), features: JSON.stringify([feature]), (data) ->
          feature_res = data.feature_results[feature]
          # feature response format: {'error': 'optional error string', 'type': 'SOME_TYPE', 'data': [stuff]}
          if feature_res.error
            console.warn(feature_res.error)
            display_text.text 'Error fetching data'
          else
            if feature_res.type is 'EASY_CHOICE'
              # display_text.text JSON.stringify(feature_res.data)
              log feature_res.data

              # setup SlickGrid
              options =
                enableCellNavigation: true
                enableColumnReorder: false

              columns = [
                id: feature
                field: feature
                name: feature
              ,
                id: 'count'
                field: 'count'
                name: 'Count'
              ]

              grid_data = _.map feature_res.data, (value, key) ->
                datapoint = {}
                datapoint[feature] = key
                datapoint['count'] = value
                datapoint

              log grid_data

              table_placeholder = $ '<div/>', class: 'slickgrid'
              display_table.append table_placeholder
              grid = new Slick.Grid(table_placeholder, grid_data, columns, options)
              grid.autosizeColumns()
            else if feature is 'year_of_birth'
              graph_placeholder = $ '<div/>', class: 'year-of-birth'
              display_graph.append graph_placeholder

              graph_data = _.map feature_res.data, (value, key) -> [parseInt(key), value]
              log graph_data

              $.plot graph_placeholder, [
                data: graph_data
              ]
            else
              console.warn("don't know how to show #{feature_res.type}")
              display_text.text 'Unavailable Metric\n' + JSON.stringify(feature_res)
