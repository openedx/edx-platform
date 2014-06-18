describe 'HTMLEditingDescriptor', ->
  beforeEach ->
    window.baseUrl = "/static/deadbeef"
    window.analytics = jasmine.createSpyObj('analytics', ['track'])
    window.course_location_analytics = jasmine.createSpy()
    window.unit_location_analytics = jasmine.createSpy()
  afterEach ->
    delete window.baseUrl
    delete window.analytics
    delete window.course_location_analytics
    delete window.unit_location_analytics
  describe 'Visual HTML Editor', ->
    beforeEach ->
      loadFixtures 'html-edit-visual.html'
      @descriptor = new HTMLEditingDescriptor($('.test-component'))
    it 'Returns data from Visual Editor if text has changed', ->
      visualEditorStub =
        getContent: () -> 'from visual editor'
      spyOn(@descriptor, 'getVisualEditor').andCallFake () ->
        visualEditorStub
      data = @descriptor.save().data
      expect(data).toEqual('from visual editor')
      expect(window.analytics.track).toHaveBeenCalledWith(
        'HTML Editor',
          'course': window.course_location_analytics
          'unit_id': window.unit_location_analytics
          'editor': 'visual'
      )
    it 'Returns data from Raw Editor if text has not changed', ->
      visualEditorStub =
        getContent: () -> '<p>original visual text</p>'
      spyOn(@descriptor, 'getVisualEditor').andCallFake () ->
        visualEditorStub
      data = @descriptor.save().data
      expect(data).toEqual('raw text')
    it 'Performs link rewriting for static assets when saving', ->
      visualEditorStub =
        getContent: () -> 'from visual editor with /c4x/foo/bar/asset/image.jpg'
      spyOn(@descriptor, 'getVisualEditor').andCallFake () ->
        visualEditorStub
      data = @descriptor.save().data
      expect(data).toEqual('from visual editor with /static/image.jpg')
    it 'When showing visual editor links are rewritten to c4x format', ->
      visualEditorStub =
        content: 'text /static/image.jpg'
        startContent: 'text /static/image.jpg'
        focus: ->
        setContent: (x) -> @content = x
        getContent: -> @content

      @descriptor.initInstanceCallback(visualEditorStub)
      expect(visualEditorStub.getContent()).toEqual('text /c4x/foo/bar/asset/image.jpg')
    it 'Calls analytics when initializing', ->
      visualEditorStub =
        getContent: -> 'content'
        setContent: (x) ->
        focus: ->
      @descriptor.initInstanceCallback(visualEditorStub)
      expect(window.analytics.track).toHaveBeenCalledWith(
        'HTML Editor',
          'course': window.course_location_analytics
          'unit_id': window.unit_location_analytics
          'editor': 'visual'
      )
    it 'Calls analytics when showing code editor', ->
      source =
        content: 'content'
      @descriptor.showCodeEditor(source)
      expect(window.analytics.track).toHaveBeenCalledWith(
        'HTML Editor: HTML',
          'course': window.course_location_analytics
          'unit_id': window.unit_location_analytics
          'editor': 'visual'
      )
    it 'Calls analytics when saving code editor', ->
      source =
        content: 'content'
      @descriptor.saveCodeEditor(source)
      expect(window.analytics.track).toHaveBeenCalledWith(
        'HTML Editor: Save',
          'course': window.course_location_analytics
          'unit_id': window.unit_location_analytics
          'editor': 'visual'
      )
  describe 'Raw HTML Editor', ->
    beforeEach ->
      loadFixtures 'html-editor-raw.html'
      @descriptor = new HTMLEditingDescriptor($('.test-component'))
    it 'Returns data from raw editor', ->
      data = @descriptor.save().data
      expect(data).toEqual('raw text')
