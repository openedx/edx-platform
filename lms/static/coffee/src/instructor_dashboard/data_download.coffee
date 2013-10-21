###
Data Download Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments
PendingInstructorTasks = -> window.InstructorDashboard.util.PendingInstructorTasks

# Data Download Section
class DataDownload
  constructor: (@$section) ->
    # gather elements
    @$display                = @$section.find '.data-display'
    @$display_text           = @$display.find '.data-display-text'
    @$display_table          = @$display.find '.data-display-table'
    @$request_response_error = @$display.find '.request-response-error'
    @$list_studs_btn = @$section.find("input[name='list-profiles']'")
    @$list_anon_btn = @$section.find("input[name='list-anon-ids']'")
    @$grade_config_btn = @$section.find("input[name='dump-gradeconf']'")

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
        @clear_display()
        @$display_table.text 'Loading...'

        # fetch user list
        $.ajax
          dataType: 'json'
          url: url
          error: std_ajax_err =>
            @clear_display()
            @$request_response_error.text "Error getting student list."
          success: (data) =>
            @clear_display()

            # display on a SlickGrid
            options =
              enableCellNavigation: true
              enableColumnReorder: false
              forceFitColumns: true

            columns = ({id: feature, field: feature, name: feature} for feature in data.queried_features)
            grid_data = data.students

            $table_placeholder = $ '<div/>', class: 'slickgrid'
            @$display_table.append $table_placeholder
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
          @$request_response_error.text "Error getting grading configuration."
        success: (data) =>
          @clear_display()
          @$display_text.html data['grading_config_summary']

    @instructor_tasks = new (PendingInstructorTasks()) @$section

  # handler for when the section title is clicked.
  onClickTitle: -> @instructor_tasks.task_poller?.start()

  # handler for when the section is closed
  onExit: -> @instructor_tasks.task_poller?.stop()

  clear_display: ->
    @$display_text.empty()
    @$display_table.empty()
    @$request_response_error.empty()


# export for use
# create parent namespaces if they do not already exist.
# abort if underscore can not be found.
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    DataDownload: DataDownload
