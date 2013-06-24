class @Logger
  # events we want sent to Segment.io for tracking
  SEGMENT_IO_WHITELIST = ["seq_goto", "seq_next", "seq_prev"]

  @log: (event_type, data) ->
    if event_type in SEGMENT_IO_WHITELIST
      # Segment.io event tracking
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
