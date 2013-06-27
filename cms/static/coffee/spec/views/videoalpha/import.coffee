describe "CMS.Views.SubtitlesImport", ->
  beforeEach ->
    # @stubModule = jasmine.createSpy("CMS.Models.Module")
    # @stubModule.id = 'stub-id'
    @message = jasmine.createSpy("CMS.Views.SubtitlesMessages")
    @importFile = jasmine.createSpy("CMS.Views.SubtitlesImportFile")
    @importYT = jasmine.createSpy("CMS.Views.SubtitlesImportYT")

    @component_location = "component_location"

    @options =
      container: $("#comp-subtitles-#{@component_location}_html_id")
      msg: @message
      modules: [
        @importFile,
        @importYT
      ]

    setFixtures """
    <div class="component" data-id="#{@component_location}">
      <div class="field comp-subtitles-entry" id="comp-subtitles-#{@component_location}_html_id">
      </div>
    </div>
    """

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
      it "submodules to be initialized", ->
        options = $.extend(true, {}, @options, {
            component_id: @component_location
            $container: @SubtitlesImport.$el
          }
        )

        $.each @options.modules, (index, module) ->
          console.log options
          expect(module).toHaveBeenCalled()
          # expect(module).toHaveBeenCalledWith options
