describe 'Logger', ->
  beforeEach ->
    window.analytics = jasmine.createSpyObj('analytics', ['track'])
    analytics.track.andCallFake(->
      $.ajax('/foo');
    )
    @requests = requests = []
    @xhr = sinon.useFakeXMLHttpRequest()
    @xhr.onCreate = (xhr) -> requests.push(xhr)
  
  afterEach ->
    @xhr.restore()
    delete window.analytics

  it 'expose window.log_event', ->
    expect(window.log_event).toBe Logger.log

  describe 'log', ->
    it 'sends an event to Segment.io, if the event is whitelisted', ->
      Logger.log 'seq_goto', 'data'
      expect(analytics.track).toHaveBeenCalledWith 'seq_goto', 'data'

    it 'send a request to log event', ->
      spyOn $, 'getWithPrefix'
      Logger.log 'example', 'data'
      expect($.getWithPrefix).toHaveBeenCalledWith '/event',
        event_type: 'example'
        event: '"data"'
        page: window.location.href

    it 'continues to log events if Segment.io is down', ->
      spyOn($, 'getWithPrefix').andCallThrough()
      Logger.log 'seq_goto', 'data'
      expect(@requests.length).toEqual 2
      expect(@requests[0].url).toMatch /foo/
      @requests[0].respond(500)
      expect($.getWithPrefix).toHaveBeenCalledWith '/event',
        event_type: 'seq_goto'
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
