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
