describe 'Logger', ->
  it 'expose window.log_event', ->
    jasmine.stubRequests()
    expect(window.log_event).toBe Logger.log

  describe 'log', ->
    it 'send a request to log event', ->
      spyOn $, 'getWithPrefix'
      Logger.log 'example', 'data'
      expect($.getWithPrefix).toHaveBeenCalledWith '/event',
        event_type: 'example'
        event: '"data"'
        page: window.location.href

  describe 'bind', ->
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
