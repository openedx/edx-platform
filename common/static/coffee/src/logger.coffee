class @Logger
  @log: (event_type, data) ->
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
