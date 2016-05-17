# Common utilities for instructor dashboard components.

# reverse arguments on common functions to enable
# better coffeescript with callbacks at the end.
plantTimeout = (ms, cb) -> setTimeout cb, ms
plantInterval = (ms, cb) -> setInterval cb, ms


# get jquery element and assert its existance
find_and_assert = ($root, selector) ->
  item = $root.find selector
  if item.length != 1
    console.error "element selection failed for '#{selector}' resulted in length #{item.length}"
    throw "Failed Element Selection"
  else
    item

# standard ajax error wrapper
#
# wraps a `handler` function so that first
# it prints basic error information to the console.
@std_ajax_err = (handler) -> (jqXHR, textStatus, errorThrown) ->
  console.warn """ajax error
                  textStatus: #{textStatus}
                  errorThrown: #{errorThrown}"""
  handler.apply this, arguments


# render a task list table to the DOM
# `$table_tasks` the $element in which to put the table
# `tasks_data`
@create_task_list_table = ($table_tasks, tasks_data) ->
  $table_tasks.empty()

  options =
    enableCellNavigation: true
    enableColumnReorder: false
    autoHeight: true
    rowHeight: 100
    forceFitColumns: true

  columns = [
    id: 'task_type'
    field: 'task_type'
    ###
    Translators: a "Task" is a background process such as grading students or sending email
    ###
    name: gettext('Task Type')
    minWidth: 102
  ,
    id: 'task_input'
    field: 'task_input'
    ###
    Translators: a "Task" is a background process such as grading students or sending email
    ###
    name: gettext('Task inputs')
    minWidth: 150
  ,
    id: 'task_id'
    field: 'task_id'
    ###
    Translators: a "Task" is a background process such as grading students or sending email
    ###
    name: gettext('Task ID')
    minWidth: 150
  ,
    id: 'requester'
    field: 'requester'
    ###
    Translators: a "Requester" is a username that requested a task such as sending email
    ###
    name: gettext('Requester')
    minWidth: 80
  ,
    id: 'created'
    field: 'created'
    ###
    Translators: A timestamp of when a task (eg, sending email) was submitted appears after this
    ###
    name: gettext('Submitted')
    minWidth: 120
  ,
    id: 'duration_sec'
    field: 'duration_sec'
    ###
    Translators: The length of a task (eg, sending email) in seconds appears this
    ###
    name: gettext('Duration (sec)')
    minWidth: 80
  ,
    id: 'task_state'
    field: 'task_state'
    ###
    Translators: The state (eg, "In progress") of a task (eg, sending email) appears after this.
    ###
    name: gettext('State')
    minWidth: 80
  ,
    id: 'status'
    field: 'status'
    ###
    Translators: a "Task" is a background process such as grading students or sending email
    ###
    name: gettext('Task Status')
    minWidth: 80
  ,
    id: 'task_message'
    field: 'task_message'
    ###
    Translators: a "Task" is a background process such as grading students or sending email
    ###
    name: gettext('Task Progress')
    minWidth: 120
  ]

  table_data = tasks_data

  $table_placeholder = $ '<div/>', class: 'slickgrid'
  $table_tasks.append $table_placeholder
  grid = new Slick.Grid($table_placeholder, table_data, columns, options)

# Formats the subject field for email content history table
subject_formatter = (row, cell, value, columnDef, dataContext) ->
  if value is null then return gettext("An error occurred retrieving your email. Please try again later, and contact technical support if the problem persists.")
  subject_text = $('<span>').text(value['subject']).html()
  return '<p><a href="#email_message_' + value['id']+ '" id="email_message_' + value['id'] + '_trig">' + subject_text + '</a></p>'

# Since sent_to is a json array, it needs some extra attention
sent_to_formatter = (row, cell, value, columnDef, dataContext) ->
  if value is null then return "<p>" + gettext("Unknown") + "</p>" else return '<p>' + value.join(", ") + '</p>'

# Formats the author, created, and number sent fields for the email content history table
unknown_if_null_formatter = (row, cell, value, columnDef, dataContext) ->
  if value is null then return "<p>" + gettext("Unknown") + "</p>" else return '<p>' + value + '</p>'

# Creates a table to display the content of bulk course emails
# sent in the past
create_email_content_table = ($table_emails, $table_emails_inner, email_data) ->
    $table_emails_inner.empty()
    $table_emails.show()

    options =
      enableCellNavigation: true
      enableColumnReorder: false
      autoHeight: true
      rowHeight: 50
      forceFitColumns: true

    columns = [
      id: 'email'
      field: 'email'
      name: gettext('Subject')
      minWidth: 80
      cssClass: "email-content-cell"
      formatter: subject_formatter
    ,
      id: 'requester'
      field: 'requester'
      name: gettext('Sent By')
      minWidth: 80
      maxWidth: 100
      cssClass: "email-content-cell"
      formatter: unknown_if_null_formatter
    ,
      id: 'sent_to'
      field: 'sent_to'
      name: gettext('Sent To')
      minWidth: 80
      maxWidth: 100
      cssClass: "email-content-cell"
      formatter: sent_to_formatter
    ,
      id: 'created'
      field: 'created'
      name: gettext('Time Sent')
      minWidth: 80
      cssClass: "email-content-cell"
      formatter: unknown_if_null_formatter
    ,
      id: 'number_sent'
      field: 'number_sent'
      name: gettext('Number Sent')
      minwidth: 100
      maxWidth: 150
      cssClass: "email-content-cell"
      formatter: unknown_if_null_formatter
    ,
    ]

    table_data = email_data

    $table_placeholder = $ '<div/>', class: 'slickgrid'
    $table_emails_inner.append $table_placeholder
    grid = new Slick.Grid($table_placeholder, table_data, columns, options)
    $table_emails.append $ '<br/>'

# Creates the modal windows linked to each email in the email history
# Displayed when instructor clicks an email's subject in the content history table
create_email_message_views = ($messages_wrapper, emails) ->
  $messages_wrapper.empty()
  for email_info in emails

    # If some error occured, bail out
    if !email_info.email then return

    # Create hidden section for modal window
    email_id = email_info.email['id']
    $message_content = $('<section>', "aria-hidden": "true", class: "modal email-modal", id: "email_message_" + email_id)
    $email_wrapper = $ '<div>', class: 'inner-wrapper email-content-wrapper'
    $email_header = $ '<div>', class: 'email-content-header'

    # Add copy email body button
    $email_header.append $('<input>', type: "button", name: "copy-email-body-text", value: gettext("Copy Email To Editor"), id: "copy_email_" + email_id)

    $close_button = $ '<a>', href: '#', class: "close-modal"
    $close_button.append $ '<i>', class: 'icon fa fa-times'
    $email_header.append $close_button

    # HTML escape the subject line
    subject_text = $('<span>').text(email_info.email['subject']).html()
    $email_header.append $('<h2>', class: "message-bold").html('<em>' + gettext('Subject:') + '</em> ' + subject_text)
    $email_header.append $('<h2>', class: "message-bold").html('<em>' + gettext('Sent By:') + '</em> ' + email_info.requester)
    $email_header.append $('<h2>', class: "message-bold").html('<em>' + gettext('Time Sent:') + '</em> ' + email_info.created)
    $email_header.append $('<h2>', class: "message-bold").html('<em>' + gettext('Sent To:') + '</em> ' + email_info.sent_to.join(", "))
    $email_wrapper.append $email_header

    $email_wrapper.append $ '<hr>'

    # Last, add email content section
    $email_content = $ '<div>', class: 'email-content-message'
    $email_content.append $('<h2>', class: "message-bold").html("<em>" + gettext("Message:") + "</em>")
    $message = $('<div>').html(email_info.email['html_message'])
    $email_content.append $message
    $email_wrapper.append $email_content

    $message_content.append $email_wrapper
    $messages_wrapper.append $message_content

    # Setup buttons to open modal window and copy an email message
    $('#email_message_' + email_info.email['id'] + '_trig').leanModal({closeButton: ".close-modal", copyEmailButton: "#copy_email_" + email_id})
    setup_copy_email_button(email_id, email_info.email['html_message'], email_info.email['subject'])

# Helper method to set click handler for modal copy email button
setup_copy_email_button = (email_id, html_message, subject) ->
    $("#copy_email_" + email_id).click =>
        editor = tinyMCE.get("mce_0")
        editor.setContent(html_message)
        $('#id_subject').val(subject)


# Helper class for managing the execution of interval tasks.
# Handles pausing and restarting.
class IntervalManager
  # Create a manager which will call `fn`
  # after a call to .start every `ms` milliseconds.
  constructor: (@ms, @fn) ->
    @intervalID = null

  # Start or restart firing every `ms` milliseconds.
  start: ->
    @fn()
    if @intervalID is null
      @intervalID = setInterval @fn, @ms

  # Pause firing.
  stop: ->
    clearInterval @intervalID
    @intervalID = null


class @PendingInstructorTasks
  ### Pending Instructor Tasks Section ####
  constructor: (@$section) ->
    # Currently running tasks
    @$running_tasks_section = find_and_assert @$section, ".running-tasks-section"
    @$table_running_tasks = find_and_assert @$section, ".running-tasks-table"
    @$no_tasks_message = find_and_assert @$section, ".no-pending-tasks-message"

    # start polling for task list
    # if the list is in the DOM
    if @$table_running_tasks.length
      # reload every 20 seconds.
      TASK_LIST_POLL_INTERVAL = 20000
      @reload_running_tasks_list()
      @task_poller = new IntervalManager(TASK_LIST_POLL_INTERVAL, => @reload_running_tasks_list())

  # Populate the running tasks list
  reload_running_tasks_list: =>
    list_endpoint = @$table_running_tasks.data 'endpoint'
    $.ajax
      dataType: 'json'
      url: list_endpoint
      success: (data) =>
        if data.tasks.length
          create_task_list_table @$table_running_tasks, data.tasks
          @$no_tasks_message.hide()
          @$running_tasks_section.show()
        else
          console.log "No pending tasks to display"
          @$running_tasks_section.hide()
          @$no_tasks_message.empty()
          @$no_tasks_message.append $('<p>').text gettext("No tasks currently running.")
          @$no_tasks_message.show()
      error: std_ajax_err => console.error "Error finding pending tasks to display"
    ### /Pending Instructor Tasks Section ####

class KeywordValidator

    @keyword_regex = /%%+[^%]+%%/g
    @keywords = ['%%USER_ID%%', '%%USER_FULLNAME%%', '%%COURSE_DISPLAY_NAME%%', '%%COURSE_END_DATE%%']

    @validate_string: (string) =>
      regex_match = string.match(@keyword_regex)
      found_keywords = if regex_match == null then [] else regex_match
      invalid_keywords = []
      is_valid = true
      keywords = @keywords

      for found_keyword in found_keywords
        do (found_keyword) ->
          if found_keyword not in keywords
            invalid_keywords.push found_keyword

      if invalid_keywords.length != 0
        is_valid = false

      return {
        is_valid: is_valid,
        invalid_keywords: invalid_keywords
      }


class ReportDownloads
  ### Report Downloads -- links expire quickly, so we refresh every 5 mins ####
  constructor: (@$section) ->

    @$report_downloads_table = @$section.find ".report-downloads-table"

    POLL_INTERVAL = 20000 # 20 seconds, just like the "pending instructor tasks" table
    @downloads_poller = new window.InstructorDashboard.util.IntervalManager(
      POLL_INTERVAL, => @reload_report_downloads()
    )

  reload_report_downloads: ->
    endpoint = @$report_downloads_table.data 'endpoint'
    $.ajax
      dataType: 'json'
      url: endpoint
      success: (data) =>
        if data.downloads.length
          @create_report_downloads_table data.downloads
        else
          console.log "No reports ready for download"
      error: (std_ajax_err) => console.error "Error finding report downloads"

  create_report_downloads_table: (report_downloads_data) ->
    @$report_downloads_table.empty()

    options =
      enableCellNavigation: true
      enableColumnReorder: false
      rowHeight: 30
      forceFitColumns: true

    columns = [
      id: 'link'
      field: 'link'
      name: gettext('File Name')
      toolTip: gettext("Links are generated on demand and expire within 5 minutes due to the sensitive nature of student information.")
      sortable: false
      minWidth: 150
      cssClass: "file-download-link"
      formatter: (row, cell, value, columnDef, dataContext) ->
        '<a target="_blank" href="' + dataContext['url'] + '">' + dataContext['name'] + '</a>'
    ]

    $table_placeholder = $ '<div/>', class: 'slickgrid'
    @$report_downloads_table.append $table_placeholder
    grid = new Slick.Grid($table_placeholder, report_downloads_data, columns, options)
    grid.onClick.subscribe(
        (event) =>
            report_url = event.target.href
            if report_url
                # Record that the user requested to download a report
                Logger.log('edx.instructor.report.downloaded', {
                    report_url: report_url
                })
    )
    grid.autosizeColumns()


# export for use
# create parent namespaces if they do not already exist.
# abort if underscore can not be found.
if _?
  _.defaults window, InstructorDashboard: {}
  window.InstructorDashboard.util =
    plantTimeout: plantTimeout
    plantInterval: plantInterval
    std_ajax_err: std_ajax_err
    IntervalManager: IntervalManager
    create_task_list_table: create_task_list_table
    create_email_content_table: create_email_content_table
    create_email_message_views: create_email_message_views
    PendingInstructorTasks: PendingInstructorTasks
    KeywordValidator: KeywordValidator
    ReportDownloads: ReportDownloads
