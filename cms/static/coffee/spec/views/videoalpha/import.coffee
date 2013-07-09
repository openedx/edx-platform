describe "CMS.Views.SubtitlesImport", ->
  beforeEach ->
    @html_id = "html_id"

    @message = jasmine.createSpy("CMS.Views.SubtitlesMessages")
    @importFile = jasmine.createSpy("CMS.Views.SubtitlesImportFile")
    @importYT = jasmine.createSpy("CMS.Views.SubtitlesImportYT")

    setFixtures """
    <div class="component" data-id="#{@html_id}">
      <div class="field comp-subtitles-entry" id="comp-subtitles-#{@html_id}">
      </div>
    </div>
    """

    @options =
      container: $("#comp-subtitles-#{@html_id}")
      msg: @message
      modules: [
        @importFile,
        @importYT
      ]

    spyOn(CMS.Views.SubtitlesImport.prototype, 'render').andCallThrough()
    @SubtitlesImport = new CMS.Views.SubtitlesImport @options

  describe "class definition", ->
    it "sets the correct tagName", ->
      expect(@SubtitlesImport.tagName).toEqual("ul")

    it "sets the correct className", ->
      expect(@SubtitlesImport.className).toEqual("comp-subtitles-import-list")

  describe "methods", ->
    describe "initialize", ->
      it "render the module", ->
        expect(CMS.Views.SubtitlesImport.prototype.render).toHaveBeenCalled()

      it "message module to be initialized", ->
        expect(@message).toHaveBeenCalled()

    describe "render", ->
      it "element is added into the DOM", ->
        expect(@options.container).toContain(@SubtitlesImport.$el)

      it "element is added with correct className", ->
        expect(@SubtitlesImport.$el).toHaveClass(@SubtitlesImport.className)

      it "submodules to be initialized", ->
        options = $.extend(true, {}, @options, {
            component_id: @html_id
            msg: @SubtitlesImport.messages
            $container: @SubtitlesImport.$el
          }
        )

        $.each @options.modules, (index, module) ->
          expect(module).toHaveBeenCalledWith options
