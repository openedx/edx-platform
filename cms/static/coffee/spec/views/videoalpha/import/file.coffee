describe "CMS.Views.SubtitlesImportFile", ->
  beforeEach ->
    @html_id = "html_id"

    $.fn.ajaxSubmit = jasmine.createSpy('$.fn.ajaxSubmit')
    @message = jasmine.createSpyObj("CMS.Views.SubtitlesMessages", [
      'render',
      'findEl'
    ])

    setFixtures """
    <ul class="comp-subtitles-import-list"></ul>
    """
    @options =
      component_id: @html_id
      msg: @message
      $container: $(".comp-subtitles-import-list")
      tpl:
        file: _.template """
          <div id="test_el"></div>
          <form action="#" class="file-upload">
            <input class="file-input" type="file" />
          </form>
        """

  describe "class definition", ->
    beforeEach ->
      @view = new CMS.Views.SubtitlesImportFile @options

    it "sets the correct tagName", ->
      expect(@view.tagName).toEqual("li")

    it "sets the correct className", ->
      expect(@view.className).toEqual("import-file")

  describe "methods", ->
    describe "initialize", ->
      beforeEach ->
        spyOn(CMS.Views.SubtitlesImportFile.prototype, 'render').andCallThrough()
        @view = new CMS.Views.SubtitlesImportFile @options
      it "render the module", ->
        expect(CMS.Views.SubtitlesImportFile.prototype.render).toHaveBeenCalled()

    describe "render", ->
      describe "if all required params exist", ->
        beforeEach ->
          @view = new CMS.Views.SubtitlesImportFile @options

        it "element is added into the DOM", ->
            expect(@options.$container).toContain(@view.$el)

        it "template is added into the DOM", ->
          expect(@options.$container).toContain('#test_el')

      describe "if params doesn't exist", ->
        beforeEach ->
          @options.tpl = null
          spyOn(window.console, "error")
          @view = new CMS.Views.SubtitlesImportFile @options

        it "template doesn't exist", ->
          expect(console.error).toHaveBeenCalledWith("Couldn't load template for file uploader")

    describe "import", ->
      beforeEach ->
        @view = new CMS.Views.SubtitlesImportFile @options

      it "files exist", ->
        @view.files = [{name: "name"}]
        @view.import()
        expect($.fn.ajaxSubmit).toHaveBeenCalledWith(
          beforeSend: @view.xhrResetProgressBar
          uploadProgress: @view.xhrProgressHandler
          complete: @view.xhrCompleteHandler
        )

      it "files doesn't exist", ->
        @view.files = []
        @view.import()
        expect($.fn.ajaxSubmit).not.toHaveBeenCalled()

    describe "events", ->
      beforeEach ->
        @view = new CMS.Views.SubtitlesImportFile @options

      it "on change file", ->
        expect(@view.$el).toHandle("change")

      it "click on 'Upload from file' button", ->
        expect(@view.$el).toHandle("click")

    describe "handlers", ->
      beforeEach ->
        @view = new CMS.Views.SubtitlesImportFile @options

      describe "xhrResetProgressBar", ->
        it "show message", ->
          @view.files = [{name: "name"}]
          options = {
            intent: 'warning'
            title: gettext("Uploading...")
            message: """
              <span class=\"file-name\">#{@view.files[0].name}</span>
              <span class=\"progress-bar\">
                  <span class=\"progress-fill\"></span>
              </span>
            """
          }
          @view.xhrResetProgressBar()
          expect(@message.render).toHaveBeenCalledWith(null, options)

      describe "xhrProgressHandler", ->
        it "show correct percentage", ->
          percentVal = 10
          @view.$progressFill = $('#test_el')
          @view.xhrProgressHandler(null, null, null, percentVal)
          percentage = @view.$progressFill.html()
          expect(percentage).toBe(percentVal + "%")

      describe "xhrCompleteHandler", ->
        it "show success message", ->
          xhr = {
            status : 200
            responseText : JSON.stringify({
              success: true
            })
          }
          @view.xhrCompleteHandler(xhr)
          expect(@message.render).toHaveBeenCalledWith('success')

        describe "show error message", ->

          it "if status is not 200", ->
            xhr = {
              status : 404
              responseText : JSON.stringify({
                success: true
              })
            }
            @view.xhrCompleteHandler(xhr)
            expect(@message.render).toHaveBeenCalledWith('error')

          it "if success flag is false", ->
            xhr = {
              status : 200
              responseText : JSON.stringify({
                success: false
              })
            }
            @view.xhrCompleteHandler(xhr)
            expect(@message.render).toHaveBeenCalledWith('error')

      describe "clickHandler", ->
        it "should preventDefault", ->
          spyOnEvent("#import-from-file", "click")
          @view.$("#import-from-file").click()
          expect("click").toHaveBeenPreventedOn("#import-from-file")

        it "value of input type file should be empty", ->
          @view.$("#import-from-file").click()
          expect(@view.$fileInput).toHaveValue('')

      describe "changeHadler", ->
        it "should preventDefault", ->
          spyOnEvent(".file-input", "change")
          @view.$fileInput.change()
          expect("change").toHaveBeenPreventedOn(".file-input")

        it "show warning message", ->
          @view.$fileInput.trigger("change")
          options =
            title: gettext("Are you sure that you want to upload the subtitle file?")
            actions:
              primary:
                click: @view.importHandler
          expect(@message.render).toHaveBeenCalledWith("warn", options)

