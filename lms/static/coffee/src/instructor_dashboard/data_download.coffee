###
Data Download Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

# Load utilities
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments
PendingInstructorTasks = -> window.InstructorDashboard.util.PendingInstructorTasks
ReportDownloads = -> window.InstructorDashboard.util.ReportDownloads

# Data Download Section
class DataDownload
  constructor: (@$section) ->
    # attach self to html so that instructor_dashboard.coffee can find
    #  this object to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @
    # gather elements
    @$list_studs_btn = @$section.find("input[name='list-profiles']'")
    @$list_studs_csv_btn = @$section.find("input[name='list-profiles-csv']'")
    @$list_may_enroll_csv_btn = @$section.find("input[name='list-may-enroll-csv']")
    @$list_anon_btn = @$section.find("input[name='list-anon-ids']'")
    @$grade_config_btn = @$section.find("input[name='dump-gradeconf']'")
    @$calculate_grades_csv_btn = @$section.find("input[name='calculate-grades-csv']'")
    @$problem_grade_report_csv_btn = @$section.find("input[name='problem-grade-report']'")

    # response areas
    @$download                        = @$section.find '.data-download-container'
    @$download_display_text           = @$download.find '.data-display-text'
    @$download_request_response_error = @$download.find '.request-response-error'
    @$reports                         = @$section.find '.reports-download-container'
    @$download_display_table          = @$reports.find '.data-display-table'
    @$reports_request_response        = @$reports.find '.request-response'
    @$reports_request_response_error  = @$reports.find '.request-response-error'

    @report_downloads = new (ReportDownloads()) @$section
    @instructor_tasks = new (PendingInstructorTasks()) @$section
    @clear_display()

    # attach click handlers
    # The list-anon case is always CSV
    @$list_anon_btn.click (e) =>
      url = @$list_anon_btn.data 'endpoint'
      location.href = url

    # this handler binds to both the download
    # and the csv button
    @$list_studs_csv_btn.click (e) =>
      @clear_display()

      url = @$list_studs_csv_btn.data 'endpoint'
      # handle csv special case
      # redirect the document to the csv file.
      url += '/csv'

      $.ajax
        dataType: 'json'
        url: url
        error: (std_ajax_err) =>
          @$reports_request_response_error.text gettext("Error generating student profile information. Please try again.")
          $(".msg-error").css({"display":"block"})
        success: (data) =>
          @$reports_request_response.text data['status']
          $(".msg-confirm").css({"display":"block"})

    @$list_studs_btn.click (e) =>
      url = @$list_studs_btn.data 'endpoint'

      # Dynamically generate slickgrid table for displaying student profile information
      @clear_display()
      @$download_display_table.text gettext('Loading')

      # fetch user list
      $.ajax
        dataType: 'json'
        url: url
        error: (std_ajax_err) =>
          @clear_display()
          @$download_request_response_error.text gettext("Error getting student list.")
        success: (data) =>
          @clear_display()

          # display on a SlickGrid
          options =
            enableCellNavigation: true
            enableColumnReorder: false
            forceFitColumns: true
            rowHeight: 35

          columns = ({id: feature, field: feature, name: data.feature_names[feature]} for feature in data.queried_features)
          grid_data = data.students

          $table_placeholder = $ '<div/>', class: 'slickgrid'
          @$download_display_table.append $table_placeholder
          grid = new Slick.Grid($table_placeholder, grid_data, columns, options)
          # grid.autosizeColumns()

    @$list_may_enroll_csv_btn.click (e) =>
      @clear_display()

      url = @$list_may_enroll_csv_btn.data 'endpoint'
      $.ajax
        dataType: 'json'
        url: url
        error: (std_ajax_err) =>
          @$reports_request_response_error.text gettext("Error generating list of students who may enroll. Please try again.")
          $(".msg-error").css({"display":"block"})
        success: (data) =>
          @$reports_request_response.text data['status']
          $(".msg-confirm").css({"display":"block"})

    @$grade_config_btn.click (e) =>
      url = @$grade_config_btn.data 'endpoint'
      # display html from grading config endpoint
      $.ajax
        dataType: 'json'
        url: url
        error: (std_ajax_err) =>
          @clear_display()
          @$download_request_response_error.text gettext("Error retrieving grading configuration.")
        success: (data) =>
          @clear_display()
          @$download_display_text.html data['grading_config_summary']

    @$calculate_grades_csv_btn.click (e) =>
      @onClickGradeDownload @$calculate_grades_csv_btn, gettext("Error generating grades. Please try again.")

    @$problem_grade_report_csv_btn.click (e) =>
      @onClickGradeDownload @$problem_grade_report_csv_btn, gettext("Error generating problem grade report. Please try again.")

  onClickGradeDownload: (button, errorMessage) ->
      # Clear any CSS styling from the request-response areas
      #$(".msg-confirm").css({"display":"none"})
      #$(".msg-error").css({"display":"none"})
      @clear_display()
      url = button.data 'endpoint'
      $.ajax
        dataType: 'json'
        url: url
        error: (std_ajax_err) =>
          @$reports_request_response_error.text errorMessage
          $(".msg-error").css({"display":"block"})
        success: (data) =>
          @$reports_request_response.text data['status']
          $(".msg-confirm").css({"display":"block"})

  # handler for when the section title is clicked.
  onClickTitle: ->
    # Clear display of anything that was here before
    @clear_display()
    @instructor_tasks.task_poller.start()
    @report_downloads.downloads_poller.start()

  # handler for when the section is closed
  onExit: ->
    @instructor_tasks.task_poller.stop()
    @report_downloads.downloads_poller.stop()

  clear_display: ->
    # Clear any generated tables, warning messages, etc.
    @$download_display_text.empty()
    @$download_display_table.empty()
    @$download_request_response_error.empty()
    @$reports_request_response.empty()
    @$reports_request_response_error.empty()
    # Clear any CSS styling from the request-response areas
    $(".msg-confirm").css({"display":"none"})
    $(".msg-error").css({"display":"none"})

# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  DataDownload: DataDownload
