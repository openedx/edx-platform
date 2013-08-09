describe 'HTMLEditingDescriptor', ->
  describe 'Read data from server, create Editor, and get data back out', ->
    it 'Does not munge &lt', ->
#     This is a test for Lighthouse #22,
#     "html names are automatically converted to the symbols they describe"
#     A better test would be a Selenium test to avoid duplicating the
#     mako template structure in html-edit-formattingbug.html.
#     However, we currently have no working Selenium tests.
      loadFixtures 'html-edit-formattingbug.html'
      @descriptor = new HTMLEditingDescriptor($('.html-edit'))
      visualEditorStub =
        isDirty: () -> false
      spyOn(@descriptor, 'getVisualEditor').andCallFake () ->
        visualEditorStub
      data = @descriptor.save().data
      expect(data).toEqual("""&lt;problem>
                           &lt;p>&lt;/p>
                           &lt;multiplechoiceresponse>
                           <pre>&lt;problem>
                               &lt;p>&lt;/p></pre>
                           <div><foo>bar</foo></div>""")
  describe 'Saves HTML', ->
    beforeEach ->
      loadFixtures 'html-edit.html'
      @descriptor = new HTMLEditingDescriptor($('.html-edit'))
    it 'Returns data from Advanced Editor if Visual Editor is not dirty', ->
      visualEditorStub =
        isDirty: () -> false
      spyOn(@descriptor, 'getVisualEditor').andCallFake () ->
        visualEditorStub
      expect(@descriptor.showingVisualEditor).toEqual(true)
      data = @descriptor.save().data
      expect(data).toEqual('Advanced Editor Text')
    it 'Returns data from Advanced Editor if Visual Editor is not showing (even if Visual Editor is dirty)', ->
      visualEditorStub =
        isDirty: () -> true
      spyOn(@descriptor, 'getVisualEditor').andCallFake () ->
        visualEditorStub
      @descriptor.showingVisualEditor = false
      data = @descriptor.save().data
      expect(data).toEqual('Advanced Editor Text')
    it 'Returns data from Visual Editor if Visual Editor is dirty and showing', ->
      visualEditorStub =
        isDirty: () -> true
        getContent: () -> 'from visual editor'
      spyOn(@descriptor, 'getVisualEditor').andCallFake () ->
        visualEditorStub
      expect(@descriptor.showingVisualEditor).toEqual(true)
      data = @descriptor.save().data
      expect(data).toEqual('from visual editor')
    it 'Performs link rewriting for static assets when saving', ->
      visualEditorStub =
        isDirty: () -> true
        getContent: () -> 'from visual editor with /c4x/foo/bar/asset/image.jpg'
      spyOn(@descriptor, 'getVisualEditor').andCallFake () ->
        visualEditorStub
      expect(@descriptor.showingVisualEditor).toEqual(true)
      @descriptor.base_asset_url = '/c4x/foo/bar/asset/'
      data = @descriptor.save().data
      expect(data).toEqual('from visual editor with /static/image.jpg')
  describe 'Can switch to Advanced Editor', ->
    beforeEach ->
      loadFixtures 'html-edit.html'
      @descriptor = new HTMLEditingDescriptor($('.html-edit'))
    it 'Populates from Visual Editor if Advanced Visual is dirty', ->
      expect(@descriptor.showingVisualEditor).toEqual(true)
      visualEditorStub =
        isDirty: () -> true
        getContent: () -> 'from visual editor'
      @descriptor.showAdvancedEditor(visualEditorStub)
      expect(@descriptor.showingVisualEditor).toEqual(false)
      expect(@descriptor.advanced_editor.getValue()).toEqual('from visual editor')
    it 'Does not populate from Visual Editor if Visual Editor is not dirty', ->
      expect(@descriptor.showingVisualEditor).toEqual(true)
      visualEditorStub =
        isDirty: () -> false
        getContent: () -> 'from visual editor'
      @descriptor.showAdvancedEditor(visualEditorStub)
      expect(@descriptor.showingVisualEditor).toEqual(false)
      expect(@descriptor.advanced_editor.getValue()).toEqual('Advanced Editor Text')
  describe 'Can switch to Visual Editor', ->
    it 'Always populates from the Advanced Editor', ->
      loadFixtures 'html-edit.html'
      @descriptor = new HTMLEditingDescriptor($('.html-edit'))
      @descriptor.showingVisualEditor = false

      visualEditorStub =
        isNotDirty: false
        content: 'not set'
        startContent: 'not set',
        focus: () -> true
        isDirty: () -> not @isNotDirty
        setContent: (x) -> @content = x
        getContent: -> @content

      @descriptor.showVisualEditor(visualEditorStub)
      expect(@descriptor.showingVisualEditor).toEqual(true)
      expect(visualEditorStub.isDirty()).toEqual(false)
      expect(visualEditorStub.getContent()).toEqual('Advanced Editor Text')
      expect(visualEditorStub.startContent).toEqual('Advanced Editor Text')
    it 'When switching to visual editor links are rewritten to c4x format', ->
      loadFixtures 'html-edit-with-links.html'
      @descriptor = new HTMLEditingDescriptor($('.html-edit'))
      @descriptor.base_asset_url = '/c4x/foo/bar/asset/'
      @descriptor.showingVisualEditor = false

      visualEditorStub =
        isNotDirty: false
        content: 'not set'
        startContent: 'not set',
        focus: () -> true
        isDirty: () -> not @isNotDirty
        setContent: (x) -> @content = x
        getContent: -> @content

      @descriptor.showVisualEditor(visualEditorStub)
      expect(@descriptor.showingVisualEditor).toEqual(true)
      expect(visualEditorStub.isDirty()).toEqual(false)
      expect(visualEditorStub.getContent()).toEqual('Advanced Editor Text with link /c4x/foo/bar/asset/dummy.jpg')
      expect(visualEditorStub.startContent).toEqual('Advanced Editor Text with link /c4x/foo/bar/asset/dummy.jpg')
