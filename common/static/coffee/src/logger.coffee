class @Logger
  # events we want sent to Segment.io for tracking
  SEGMENT_IO_WHITELIST = ["seq_goto", "seq_next", "seq_prev", "problem_check", "problem_reset", "problem_show", "problem_save"]

  @log: (event_type, data) ->
    # Segment.io event tracking
    if event_type in SEGMENT_IO_WHITELIST
      # to avoid changing the format of data sent to our servers, we only massage it here
      if typeof data isnt 'object' or data is null
        analytics.track event_type, value: data
      else
        analytics.track event_type, data

    $.getWithPrefix '/event',
      event_type: event_type
      event: JSON.stringify(data)
      page: window.location.href

  @bind: ->
    window.onunload = ->
      $.ajaxWithPrefix
        url: "/event"
        data:
          event_type: 'page_close'
          event: ''
          page: window.location.href
        async: false

# Keeping this for conpatibility issue only.
@log_event = Logger.log
