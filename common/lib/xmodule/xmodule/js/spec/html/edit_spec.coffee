describe 'HTMLEditingDescriptor', ->
  beforeEach ->
    window.baseUrl = "/static/deadbeef"
  afterEach ->
    delete window.baseUrl
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
    it 'Enables spellcheck', ->
      expect($('.html-editor iframe')[0].contentDocument.body.spellcheck).toBe(true)
  describe 'Raw HTML Editor', ->
    beforeEach ->
      loadFixtures 'html-editor-raw.html'
      @descriptor = new HTMLEditingDescriptor($('.test-component'))
    it 'Returns data from raw editor', ->
      data = @descriptor.save().data
      expect(data).toEqual('raw text')
