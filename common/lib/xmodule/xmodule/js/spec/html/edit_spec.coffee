describe 'HTMLEditingDescriptor', ->
  beforeEach ->
    window.baseUrl = "/static/deadbeef"
  afterEach ->
    delete window.baseUrl
  describe 'HTML Editor', ->
    beforeEach ->
      loadFixtures 'html-edit.html'
      @descriptor = new HTMLEditingDescriptor($('.html-edit'))
    it 'Returns data from Visual Editor if Visual Editor is dirty', ->
      visualEditorStub =
        isDirty: () -> true
        getContent: () -> 'from visual editor'
      spyOn(@descriptor, 'getVisualEditor').andCallFake () ->
        visualEditorStub
      data = @descriptor.save().data
      expect(data).toEqual('from visual editor')
    it 'Returns data from Visual Editor even if Visual Editor is not dirty', ->
      visualEditorStub =
        isDirty: () -> false
        getContent: () -> 'from visual editor'
      spyOn(@descriptor, 'getVisualEditor').andCallFake () ->
        visualEditorStub
      data = @descriptor.save().data
      expect(data).toEqual('from visual editor')
    it 'Performs link rewriting for static assets when saving', ->
      visualEditorStub =
        isDirty: () -> true
        getContent: () -> 'from visual editor with /c4x/foo/bar/asset/image.jpg'
      spyOn(@descriptor, 'getVisualEditor').andCallFake () ->
        visualEditorStub
      @descriptor.base_asset_url = '/c4x/foo/bar/asset/'
      data = @descriptor.save().data
      expect(data).toEqual('from visual editor with /static/image.jpg')
    it 'When showing visual editor links are rewritten to c4x format', ->
      @descriptor = new HTMLEditingDescriptor($('.html-edit'))
      @descriptor.base_asset_url = '/c4x/foo/bar/asset/'

      visualEditorStub =
        content: 'text /static/image.jpg'
        startContent: 'text /static/image.jpg'
        focus: ->
        setContent: (x) -> @content = x
        getContent: -> @content

      @descriptor.initInstanceCallback(visualEditorStub)
      expect(visualEditorStub.getContent()).toEqual('text /c4x/foo/bar/asset/image.jpg')
