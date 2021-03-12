describe('HTMLEditingDescriptor', function() {
  beforeEach(() => window.baseUrl = "/static/deadbeef/");
  afterEach(() => delete window.baseUrl);
  describe('Visual HTML Editor', function() {
    beforeEach(function() {
      loadFixtures('html-edit-visual.html');
      this.descriptor = new HTMLEditingDescriptor($('.test-component'));
    });
    it('Returns data from Visual Editor if text has changed', function() {
      const visualEditorStub =
        {getContent() { return 'from visual editor'; }};
      spyOn(this.descriptor, 'getVisualEditor').and.callFake(() => visualEditorStub);
      const { data } = this.descriptor.save();
      expect(data).toEqual('from visual editor');
    });
    it('Returns data from Raw Editor if text has not changed', function() {
      const visualEditorStub =
        {getContent() { return '<p>original visual text</p>'; }};
      spyOn(this.descriptor, 'getVisualEditor').and.callFake(() => visualEditorStub);
      const { data } = this.descriptor.save();
      expect(data).toEqual('raw text');
    });
    it('Performs link rewriting for static assets when saving', function() {
      const visualEditorStub =
        {getContent() { return 'from visual editor with /c4x/foo/bar/asset/image.jpg'; }};
      spyOn(this.descriptor, 'getVisualEditor').and.callFake(() => visualEditorStub);
      const { data } = this.descriptor.save();
      expect(data).toEqual('from visual editor with /static/image.jpg');
    });
    it('When showing visual editor links are rewritten to c4x format', function() {
      const visualEditorStub = {
        content: 'text /static/image.jpg',
        startContent: 'text /static/image.jpg',
        focus() {},
        setContent(x) { this.content = x; },
        getContent() { return this.content; }
      };

      this.descriptor.initInstanceCallback(visualEditorStub);
      expect(visualEditorStub.getContent()).toEqual('text /c4x/foo/bar/asset/image.jpg');
    });
    it('Enables spellcheck', () => expect($('.html-editor iframe')[0].contentDocument.body.spellcheck).toBe(true));
    it('Retains ascii characters', function() {
      const editorData = '<a href="/static/Programación_Gas.pptx">fóó</a>';
      const expectedData = '<p><a href="/static/Programación_Gas.pptx">fóó</a></p>'

      this.descriptor.getVisualEditor().setContent(editorData)
      const savedContent = this.descriptor.getVisualEditor().getContent()
      expect(savedContent).toEqual(expectedData);
    });
    it('Editor base URL does not contain double slash', function(){
      const editor = this.descriptor.getVisualEditor();
      expect(editor.editorManager.baseURL).not.toContain('//');
    });
  });
  describe('Raw HTML Editor', function() {
    beforeEach(function() {
      loadFixtures('html-editor-raw.html');
      this.descriptor = new HTMLEditingDescriptor($('.test-component'));
    });
    it('Returns data from raw editor', function() {
      const { data } = this.descriptor.save();
      expect(data).toEqual('raw text');
    });
  });
});
