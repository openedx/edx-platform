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

# Data Download Certificate issued
class @DataDownload_Certificate
  constructor: (@$container) ->
    # gather elements
    @$list_issued_certificate_table_btn = @$container.find("input[name='issued-certificates-list']")
    @$list_issued_certificate_csv_btn = @$container.find("input[name='issued-certificates-csv']")
    @$certificate_display_table       = @$container.find '.certificate-data-display-table'
    @$certificates_request_response_error  = @$container.find '.issued-certificates-error.request-response-error'


    @$list_issued_certificate_table_btn.click (e) =>
      url = @$list_issued_certificate_table_btn.data 'endpoint'
      # Dynamically generate slickgrid table for displaying issued certificate information.
      @clear_ui()
      @$certificate_display_table.text gettext('Loading data...')
      # fetch user list
      $.ajax
        type: 'POST'
        url: url
        error: (std_ajax_err) =>
          @clear_ui()
          @$certificates_request_response_error.text gettext("Error getting issued certificates list.")
          $(".issued_certificates .issued-certificates-error.msg-error").css({"display":"block"})
        success: (data) =>
          @clear_ui()
          # display on a SlickGrid
          options =
            enableCellNavigation: true
            enableColumnReorder: false
            forceFitColumns: true
            rowHeight: 35

          columns = ({id: feature, field: feature, name: data.feature_names[feature]} for feature in data.queried_features)
          grid_data = data.certificates

          $table_placeholder = $ '<div/>', class: 'slickgrid'
          @$certificate_display_table.append $table_placeholder
          new Slick.Grid($table_placeholder, grid_data, columns, options)

    @$list_issued_certificate_csv_btn.click (e) =>
      @clear_ui()
      url = @$list_issued_certificate_csv_btn.data 'endpoint'
      location.href = url + '?csv=true'

  clear_ui: ->
    # Clear any generated tables, warning messages, etc of certificates.
    @$certificate_display_table.empty()
    @$certificates_request_response_error.empty()
    $(".issued-certificates-error.msg-error").css({"display":"none"})

# Data Download Section
class DataDownload
  constructor: (@$section) ->
    # attach self to html so that instructor_dashboard.coffee can find
    #  this object to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @

    # isolate # initialize DataDownload_Certificate subsection
    new DataDownload_Certificate @$section.find '.issued_certificates'

    # gather elements
    @$list_studs_btn = @$section.find("input[name='list-profiles']")
    @$list_studs_csv_btn = @$section.find("input[name='list-profiles-csv']")
    @$list_proctored_exam_results_csv_btn = @$section.find("input[name='proctored-exam-results-report']")
    @$survey_results_csv_btn = @$section.find("input[name='survey-results-report']")
    @$list_may_enroll_csv_btn = @$section.find("input[name='list-may-enroll-csv']")
    @$list_problem_responses_csv_input = @$section.find("input[name='problem-location']")
    @$list_problem_responses_csv_btn = @$section.find("input[name='list-problem-responses-csv']")
    @$list_anon_btn = @$section.find("input[name='list-anon-ids']")
    @$grade_config_btn = @$section.find("input[name='dump-gradeconf']")
    @$calculate_grades_csv_btn = @$section.find("input[name='calculate-grades-csv']")
    @$problem_grade_report_csv_btn = @$section.find("input[name='problem-grade-report']")
    @$async_report_btn = @$section.find("input[class='async-report-btn']")

    # response areas
    @$download                        = @$section.find '.data-download-container'
    @$download_display_text           = @$download.find '.data-display-text'
    @$download_request_response_error = @$download.find '.request-response-error'
    @$reports                         = @$section.find '.reports-download-container'
    @$download_display_table          = @$reports.find '.profile-data-display-table'
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

    # attach click handlers
    # The list_proctored_exam_results case is always CSV
    @$list_proctored_exam_results_csv_btn.click (e) =>
      url = @$list_proctored_exam_results_csv_btn.data 'endpoint'
      # display html from proctored exam results config endpoint
      $.ajax
        type: 'POST'
        dataType: 'json'
        url: url
        error: (std_ajax_err) =>
          @clear_display()
          @$reports_request_response_error.text gettext(
            "Error generating proctored exam results. Please try again."
          )
          $(".msg-error").css({"display":"block"})
        success: (data) =>
          @clear_display()
          @$reports_request_response.text data['status']
          $(".msg-confirm").css({"display":"block"})

    # attach click handlers
    # The list_proctored_exam_results case is always CSV
    @$survey_results_csv_btn.click (e) =>
      url = @$survey_results_csv_btn.data 'endpoint'
      # display html from survey results config endpoint
      $.ajax
        type: 'POST'
        dataType: 'json'
        url: url
        error: (std_ajax_err) =>
          @clear_display()
          @$reports_request_response_error.text gettext(
            "Error generating survey results. Please try again."
          )
          $(".msg-error").css({"display":"block"})
        success: (data) =>
          @clear_display()
          @$reports_request_response.text data['status']
          $(".msg-confirm").css({"display":"block"})

    # this handler binds to both the download
    # and the csv button
    @$list_studs_csv_btn.click (e) =>
      @clear_display()

      url = @$list_studs_csv_btn.data 'endpoint'
      # handle csv special case
      # redirect the document to the csv file.
      url += '/csv'

      $.ajax
        type: 'POST'
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
        type: 'POST'
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

    @$list_problem_responses_csv_btn.click (e) =>
      @clear_display()

      url = @$list_problem_responses_csv_btn.data 'endpoint'
      $.ajax
        type: 'POST'
        dataType: 'json'
        url: url
        data:
          problem_location: @$list_problem_responses_csv_input.val()
        error: (std_ajax_err) =>
          @$reports_request_response_error.text JSON.parse(std_ajax_err['responseText'])
          $(".msg-error").css({"display":"block"})
        success: (data) =>
          @$reports_request_response.text data['status']
          $(".msg-confirm").css({"display":"block"})

    @$list_may_enroll_csv_btn.click (e) =>
      @clear_display()

      url = @$list_may_enroll_csv_btn.data 'endpoint'
      $.ajax
        type: 'POST'
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
        type: 'POST'
        dataType: 'json'
        url: url
        error: (std_ajax_err) =>
          @clear_display()
          @$download_request_response_error.text gettext("Error retrieving grading configuration.")
        success: (data) =>
          @clear_display()
          @$download_display_text.html data['grading_config_summary']

    @$async_report_btn.click (e) =>
        # Clear any CSS styling from the request-response areas
        #$(".msg-confirm").css({"display":"none"})
        #$(".msg-error").css({"display":"none"})
        @clear_display()
        url = $(e.target).data 'endpoint'
        $.ajax
          type: 'POST'
          dataType: 'json'
          url: url
          error: std_ajax_err =>
            if e.target.name == 'calculate-grades-csv'
              @$grades_request_response_error.text gettext("Error generating grades. Please try again.")
            else if e.target.name == 'problem-grade-report'
              @$grades_request_response_error.text gettext("Error generating problem grade report. Please try again.")
            else if e.target.name == 'export-ora2-data'
              @$grades_request_response_error.text gettext("Error generating ORA data report. Please try again.")
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
