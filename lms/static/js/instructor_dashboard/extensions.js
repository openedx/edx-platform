###
Extensions Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments

# Extensions Section
class Extensions

  constructor: (@$section) ->
    # attach self to html
    # so that instructor_dashboard.coffee can find this object
    # to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @

    # Gather buttons
    @$change_due_date = @$section.find("input[name='change-due-date']")
    @$reset_due_date = @$section.find("input[name='reset-due-date']")
    @$show_unit_extensions = @$section.find("input[name='show-unit-extensions']")
    @$show_student_extensions = @$section.find("input[name='show-student-extensions']")

    # Gather notification areas
    @$section.find(".request-response").hide()
    @$section.find(".request-response-error").hide()

    # Gather grid elements
    $grid_display = @$section.find '.data-display'
    @$grid_text = $grid_display.find '.data-display-text'
    @$grid_table = $grid_display.find '.data-display-table'

    # Click handlers
    @$change_due_date.click =>
      @clear_display()
      @$student_input = @$section.find("#set-extension input[name='student']")
      @$url_input = @$section.find("#set-extension select[name='url']")
      @$due_datetime_input = @$section.find("#set-extension input[name='due_datetime']")
      send_data =
        student: @$student_input.val()
        url: @$url_input.val()
        due_datetime: @$due_datetime_input.val()

      $.ajax
        type: 'POST'
        dataType: 'json'
        url: @$change_due_date.data 'endpoint'
        data: send_data
        success: (data) => @display_response "set-extension", data
        error: (xhr) => @fail_with_error "set-extension", "Error changing due date", xhr

    @$reset_due_date.click =>
      @clear_display()
      @$student_input = @$section.find("#reset-extension input[name='student']")
      @$url_input = @$section.find("#reset-extension select[name='url']")
      send_data =
        student: @$student_input.val()
        url: @$url_input.val()

      $.ajax
        type: 'POST'
        dataType: 'json'
        url: @$reset_due_date.data 'endpoint'
        data: send_data
        success: (data) => @display_response "reset-extension", data
        error: (xhr) => @fail_with_error "reset-extension", "Error reseting due date", xhr

    @$show_unit_extensions.click =>
      @clear_display()
      @$grid_table.text 'Loading'

      @$url_input = @$section.find("#view-granted-extensions select[name='url']")
      url = @$show_unit_extensions.data 'endpoint'
      send_data =
        url: @$url_input.val()
      $.ajax
        type: 'POST'
        dataType: 'json'
        url: url
        data: send_data
        error: (xhr) => @fail_with_error "view-granted-extensions", "Error getting due dates", xhr
        success: (data) => @display_grid data

    @$show_student_extensions.click =>
      @clear_display()
      @$grid_table.text 'Loading'

      url = @$show_student_extensions.data 'endpoint'
      @$student_input = @$section.find("#view-granted-extensions input[name='student']")
      send_data =
        student: @$student_input.val()
      $.ajax
        type: 'POST'
        dataType: 'json'
        url: url
        data: send_data
        error: (xhr) => @fail_with_error "view-granted-extensions", "Error getting due dates", xhr
        success: (data) => @display_grid data
      
  # handler for when the section title is clicked.
  onClickTitle: ->

  fail_with_error: (id, msg, xhr) ->
    $task_error = @$section.find("#" + id + " .request-response-error")
    $task_response = @$section.find("#" + id + " .request-response")
    @clear_display()
    data = $.parseJSON xhr.responseText
    msg += ": " + data['error']
    console.warn msg
    $task_response.empty()
    $task_error.empty()
    $task_error.text msg
    $task_error.show()

  display_response: (id, data) ->
    $task_error = @$section.find("#" + id + " .request-response-error")
    $task_response = @$section.find("#" + id + " .request-response")
    $task_error.empty().hide()
    $task_response.empty().text data
    $task_response.show()

  display_grid: (data) ->
    @clear_display()
    @$grid_text.text data.title

    # display on a SlickGrid
    options =
      enableCellNavigation: true
      enableColumnReorder: false
      forceFitColumns: true

    columns = ({id: col, field: col, name: col} for col in data.header)
    grid_data = data.data

    $table_placeholder = $ '<div/>', class: 'slickgrid', style: 'min-height: 400px'
    @$grid_table.append $table_placeholder
    grid = new Slick.Grid($table_placeholder, grid_data, columns, options)

  clear_display: ->
    @$grid_text.empty()
    @$grid_table.empty()
    @$section.find(".request-response-error").empty().hide()
    @$section.find(".request-response").empty().hide()

# export for use
# create parent namespaces if they do not already exist.
# abort if underscore can not be found.
if _?
  _.defaults window, InstructorDashboard: {}
  _.defaults window.InstructorDashboard, sections: {}
  _.defaults window.InstructorDashboard.sections,
    Extensions: Extensions
