###
Data Download Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

# Load utilities
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments
PendingInstructorTasks = -> window.InstructorDashboard.util.PendingInstructorTasks

# Data Download Section
class DataDownload
  constructor: (@$section) ->
    # attach self to html so that instructor_dashboard.coffee can find
    #  this object to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @
    # gather elements
    @$list_studs_btn = @$section.find("input[name='list-profiles']'")
    @$list_anon_btn = @$section.find("input[name='list-anon-ids']'")
    @$grade_config_btn = @$section.find("input[name='dump-gradeconf']'")
    @$calculate_grades_csv_btn = @$section.find("input[name='calculate-grades-csv']'")

    # response areas
    @$download                        = @$section.find '.data-download-container'
    @$download_display_text           = @$download.find '.data-display-text'
    @$download_display_table          = @$download.find '.data-display-table'
    @$download_request_response_error = @$download.find '.request-response-error'
    @$grades                        = @$section.find '.grades-download-container'
    @$grades_request_response       = @$grades.find '.request-response'
    @$grades_request_response_error = @$grades.find '.request-response-error'

    @grade_downloads = new GradeDownloads(@$section)
    @instructor_tasks = new (PendingInstructorTasks()) @$section
    @clear_display()

    # attach click handlers
    # The list-anon case is always CSV
    @$list_anon_btn.click (e) =>
      url = @$list_anon_btn.data 'endpoint'
      location.href = url

    # this handler binds to both the download
    # and the csv button
    @$list_studs_btn.click (e) =>
      url = @$list_studs_btn.data 'endpoint'

      # handle csv special case
      if $(e.target).data 'csv'
        # redirect the document to the csv file.
        url += '/csv'
        location.href = url
      else
        # Dynamically generate slickgrid table for displaying student profile information
        @clear_display()
        @$download_display_table.text gettext('Loading...')

        # fetch user list
        $.ajax
          dataType: 'json'
          url: url
          error: std_ajax_err =>
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

            columns = ({id: feature, field: feature, name: feature} for feature in data.queried_features)
            grid_data = data.students

            $table_placeholder = $ '<div/>', class: 'slickgrid'
            @$download_display_table.append $table_placeholder
            grid = new Slick.Grid($table_placeholder, grid_data, columns, options)
            # grid.autosizeColumns()

    @$grade_config_btn.click (e) =>
      url = @$grade_config_btn.data 'endpoint'
      # display html from grading config endpoint
      $.ajax
        dataType: 'json'
        url: url
        error: std_ajax_err =>
          @clear_display()
          @$download_request_response_error.text gettext("Error retrieving grading configuration.")
        success: (data) =>
          @clear_display()
          @$download_display_text.html data['grading_config_summary']

    @$calculate_grades_csv_btn.click (e) =>
      # Clear any CSS styling from the request-response areas
      #$(".msg-confirm").css({"display":"none"})
      #$(".msg-error").css({"display":"none"})
      @clear_display()
      url = @$calculate_grades_csv_btn.data 'endpoint'
      $.ajax
        dataType: 'json'
        url: url
        error: std_ajax_err =>
          @$grades_request_response_error.text gettext("Error generating grades. Please try again.")
          $(".msg-error").css({"display":"block"})
        success: (data) =>
          @$grades_request_response.text data['status']
          $(".msg-confirm").css({"display":"block"})

  # handler for when the section title is clicked.
  onClickTitle: ->
    # Clear display of anything that was here before
    @clear_display()
    @instructor_tasks.task_poller.start()
    @grade_downloads.downloads_poller.start()

  # handler for when the section is closed
  onExit: ->
    @instructor_tasks.task_poller.stop()
    @grade_downloads.downloads_poller.stop()

  clear_display: ->
    # Clear any generated tables, warning messages, etc.
    @$download_display_text.empty()
    @$download_display_table.empty()
    @$download_request_response_error.empty()
    @$grades_request_response.empty()
    @$grades_request_response_error.empty()
    # Clear any CSS styling from the request-response areas
    $(".msg-confirm").css({"display":"none"})
    $(".msg-error").css({"display":"none"})


class GradeDownloads
  ### Grade Downloads -- links expire quickly, so we refresh every 5 mins ####
  constructor: (@$section) ->


    @$grades                        = @$section.find '.grades-download-container'
    @$grades_request_response       = @$grades.find '.request-response'
    @$grades_request_response_error = @$grades.find '.request-response-error'
    @$grade_downloads_table         = @$grades.find ".grade-downloads-table"

    POLL_INTERVAL = 1000 * 60 * 5 # 5 minutes in ms
    @downloads_poller = new window.InstructorDashboard.util.IntervalManager(
      POLL_INTERVAL, => @reload_grade_downloads()
    )

  reload_grade_downloads: ->
    endpoint = @$grade_downloads_table.data 'endpoint'
    $.ajax
      dataType: 'json'
      url: endpoint
      success: (data) =>
        if data.downloads.length
          @create_grade_downloads_table data.downloads
        else
          console.log "No grade CSVs ready for download"
      error: std_ajax_err => console.error "Error finding grade download CSVs"

  create_grade_downloads_table: (grade_downloads_data) ->
    @$grade_downloads_table.empty()

    options =
      enableCellNavigation: true
      enableColumnReorder: false
      rowHeight: 30
      forceFitColumns: true

    columns = [
      id: 'link'
      field: 'link'
      name: gettext('File Name (Newest First)')
      toolTip: gettext("Links are generated on demand and expire within 5 minutes due to the sensitive nature of student grade information.")
      sortable: false
      minWidth: 150
      cssClass: "file-download-link"
      formatter: (row, cell, value, columnDef, dataContext) ->
        '<a href="' + dataContext['url'] + '">' + dataContext['name'] + '</a>'
    ]

    $table_placeholder = $ '<div/>', class: 'slickgrid'
    @$grade_downloads_table.append $table_placeholder
    grid = new Slick.Grid($table_placeholder, grade_downloads_data, columns, options)
    grid.autosizeColumns()


# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  DataDownload: DataDownload
