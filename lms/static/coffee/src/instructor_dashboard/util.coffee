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
std_ajax_err = (handler) -> (jqXHR, textStatus, errorThrown) ->
  console.warn """ajax error
                  textStatus: #{textStatus}
                  errorThrown: #{errorThrown}"""
  handler.apply this, arguments


# render a task list table to the DOM
# `$table_tasks` the $element in which to put the table
# `tasks_data`
create_task_list_table = ($table_tasks, tasks_data) ->
  $table_tasks.empty()

  options =
    enableCellNavigation: true
    enableColumnReorder: false
    autoHeight: true
    rowHeight: 60
    forceFitColumns: true

  columns = [
    id: 'task_type'
    field: 'task_type'
    name: 'Task Type'
    minWidth: 100
  ,
    id: 'task_input'
    field: 'task_input'
    name: 'Task inputs'
    minWidth: 150
  ,
    id: 'task_id'
    field: 'task_id'
    name: 'Task ID'
    minWidth: 150
  ,
    id: 'requester'
    field: 'requester'
    name: 'Requester'
    minWidth: 80
  ,
    id: 'created'
    field: 'created'
    name: 'Submitted'
    minWidth: 120
  ,
    id: 'duration_sec'
    field: 'duration_sec'
    name: 'Duration (sec)'
    minWidth: 80
  ,
    id: 'task_state'
    field: 'task_state'
    name: 'State'
    minWidth: 80
  ,
    id: 'status'
    field: 'status'
    name: 'Task Status'
    minWidth: 80
  ,
    id: 'task_message'
    field: 'task_message'
    name: 'Task Progress'
    minWidth: 120
  ]

  table_data = tasks_data

  $table_placeholder = $ '<div/>', class: 'slickgrid'
  $table_tasks.append $table_placeholder
  grid = new Slick.Grid($table_placeholder, table_data, columns, options)

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


class PendingInstructorTasks
  ### Pending Instructor Tasks Section ####
  constructor: (@$section) ->
    # Currently running tasks
    @$table_running_tasks = find_and_assert @$section, ".running-tasks-table"

    # start polling for task list
    # if the list is in the DOM
    if @$table_running_tasks.length > 0
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
      success: (data) => create_task_list_table @$table_running_tasks, data.tasks
      error: std_ajax_err => console.warn "error listing all instructor tasks"
    ### /Pending Instructor Tasks Section ####

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
    PendingInstructorTasks: PendingInstructorTasks
