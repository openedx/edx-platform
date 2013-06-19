describe 'Logger', ->
  it 'expose window.log_event', ->
    expect(window.log_event).toBe Logger.log

  describe 'log', ->
    it 'sends an event to Segment.io, if the event is whitelisted', ->
      spyOn(analytics, 'track')
      Logger.log 'seq_goto', 'data'
      expect(analytics.track).toHaveBeenCalledWith 'seq_goto', 'data'

    it 'send a request to log event', ->
      spyOn $, 'getWithPrefix'
      Logger.log 'example', 'data'
      expect($.getWithPrefix).toHaveBeenCalledWith '/event',
        event_type: 'example'
        event: '"data"'
        page: window.location.href

  # Broken with commit 9f75e64? Skipping for now.
  xdescribe 'bind', ->
    beforeEach ->
      Logger.bind()
      Courseware.prefix = '/6002x'

    afterEach ->
      window.onunload = null

    it 'bind the onunload event', ->
      expect(window.onunload).toEqual jasmine.any(Function)

    it 'send a request to log event', ->
      spyOn($, 'ajax')
      window.onunload()
      expect($.ajax).toHaveBeenCalledWith
        url: "#{Courseware.prefix}/event",
        data:
          event_type: 'page_close'
          event: ''
          page: window.location.href
        async: false
