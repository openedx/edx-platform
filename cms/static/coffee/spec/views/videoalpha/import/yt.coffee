describe "CMS.Views.SubtitlesImportYT", ->
  beforeEach ->
    @html_id = "html_id"

    spyOn($, 'ajax')
    @message = jasmine.createSpyObj("CMS.Views.SubtitlesMessages", [
      'render'
    ])

    setFixtures """
    <ul class="comp-subtitles-import-list"></ul>
    """
    @options =
      component_id: @html_id
      msg: @message
      $container: $(".comp-subtitles-import-list")

  describe "class definition", ->
    beforeEach ->
      @view = new CMS.Views.SubtitlesImportYT @options

    it "sets the correct tagName", ->
      expect(@view.tagName).toEqual("li")

    it "sets the correct className", ->
      expect(@view.className).toEqual("import-youtube")

  describe "methods", ->
    describe "initialize", ->
      beforeEach ->
        spyOn(CMS.Views.SubtitlesImportYT.prototype, 'render').andCallThrough()
        @view = new CMS.Views.SubtitlesImportYT @options
      it "render the module", ->
        expect(CMS.Views.SubtitlesImportYT.prototype.render).toHaveBeenCalled()

    describe "render", ->
      beforeEach ->
        @view = new CMS.Views.SubtitlesImportYT @options

      it "element is added into the DOM", ->
          expect(@options.$container).toContain(@view.$el)

      it "button is added", ->
        expect(@view.$el).toContain('a')

    describe "import", ->
      beforeEach ->
        @view = new CMS.Views.SubtitlesImportYT @options

      it "show wait message", ->
        @view.import()
        expect(@message.render).toHaveBeenCalledWith('wait')

      it "ajax is called", ->
        option =
          url: @view.url
          type: "POST"
          dataType: "json"
          contentType: "application/json"
          timeout: 1000*60
          data: JSON.stringify(
              'id': @html_id
          )
          success: @view.xhrSuccessHandler
          error: @view.xhrErrorHandler

        @view.import()
        expect($.ajax).toHaveBeenCalledWith(option)

    describe "events", ->
      beforeEach ->
        @view = new CMS.Views.SubtitlesImportYT @options

      it "click on 'Import from Youtube' button", ->
        expect(@view.$el).toHandle("click")

    describe "handlers", ->
      beforeEach ->
        @view = new CMS.Views.SubtitlesImportYT @options

      describe "clickHandler", ->
        it "should preventDefault", ->
          spyOnEvent("#import-from-youtube", "click")
          @view.$("#import-from-youtube").click()
          expect("click").toHaveBeenPreventedOn("#import-from-youtube")

        it "show warn message", ->
          options =
            title: gettext('''
              Are you sure that you want to import the subtitle file
              found on YouTube?
            ''')
            actions:
              primary:
                click: @view.importHandler

          @view.$('#import-from-youtube').click()
          expect(@message.render).toHaveBeenCalledWith("warn", options)

      describe "xhrErrorHandler", ->
        it "show error message", ->
          @view.xhrErrorHandler()
          expect(@message.render).toHaveBeenCalledWith("error")

      describe "xhrSuccessHandler", ->
        it "show success message", ->
          @view.xhrSuccessHandler({
            success: true
          })
          expect(@message.render).toHaveBeenCalledWith("success")

        it "show error message", ->
          @view.xhrSuccessHandler({
            success: false
          })
          expect(@message.render).toHaveBeenCalledWith("error")
