class @Logger

  # listeners[event_type][element] -> list of callbacks
  listeners = {}
  @log: (event_type, data, element = null) ->
    # Check to see if we're listening for the event type.
    if event_type of listeners
      # Cool.  Do the elements also match?
      # null element in the listener dictionary means any element will do.
      # null element in the @log call means we don't know the element name.
      if null of listeners[event_type]
        # Make the callbacks.
        for callback in listeners[event_type][null]
          callback(event_type, data, element)
      else if element of listeners[event_type]
        for callback in listeners[event_type][element]
          callback(event_type, data, element)

    # Regardless of whether any callbacks were made, log this event.
    $.postWithPrefix '/event',
      event_type: event_type
      event: JSON.stringify(data)
      page: window.location.href

  @listen: (event_type, element, callback) ->
    # Add a listener.  If you want any element to trigger this listener,
    # do element = null
    if event_type not of listeners
      listeners[event_type] = {}
    if element not of listeners[event_type]
      listeners[event_type][element] = [callback]
    else
      listeners[event_type][element].push callback

  @bind: ->
    window.onunload = ->
      $.ajaxWithPrefix
        url: "/event"
        data:
          event_type: 'page_close'
          event: ''
          page: window.location.href
        async: false


# log_event exists for compatibility reasons
# and will soon be deprecated.
@log_event = Logger.log
