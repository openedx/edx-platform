# Common utilities for instructor dashboard components.

# reverse arguments on common functions to enable
# better coffeescript with callbacks at the end.
plantTimeout = (ms, cb) -> setTimeout cb, ms
plantInterval = (ms, cb) -> setInterval cb, ms


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
  ,
    id: 'requester'
    field: 'requester'
    name: 'Requester'
    width: 30
  ,
    id: 'task_input'
    field: 'task_input'
    name: 'Input'
  ,
    id: 'task_state'
    field: 'task_state'
    name: 'State'
    width: 30
  ,
    id: 'task_id'
    field: 'task_id'
    name: 'Task ID'
    width: 50
  ,
    id: 'created'
    field: 'created'
    name: 'Created'
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
  # Soes not fire immediately.
  start: ->
    if @intervalID is null
      @intervalID = setInterval @fn, @ms

  # Pause firing.
  stop: ->
    clearInterval @intervalID
    @intervalID = null


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
