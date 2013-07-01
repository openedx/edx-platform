describe "CMS.Views.DownloadSubtitles", ->
  beforeEach ->
    @html_id = "html_id"

    setFixtures """
    <ul class="comp-subtitles-import-list"></ul>
    """
    @options =
      component_id: @html_id
      msg: @message
      $container: $(".comp-subtitles-import-list")
      subtitlesExist: true

  describe "class definition", ->
    beforeEach ->
      @view = new CMS.Views.DownloadSubtitles @options

    it "sets the correct tagName", ->
      expect(@view.tagName).toEqual("li")

    it "sets the correct className", ->
      expect(@view.className).toEqual("download-file")

  describe "methods", ->
    describe "initialize", ->
      beforeEach ->
        spyOn(CMS.Views.DownloadSubtitles.prototype, 'render').andCallThrough()
        @view = new CMS.Views.DownloadSubtitles @options

      it "render the module", ->
        expect(CMS.Views.DownloadSubtitles.prototype.render).toHaveBeenCalled()

    describe "render", ->
      describe "subtitles exist", ->

        beforeEach ->
          @view = new CMS.Views.DownloadSubtitles @options

        it "button is added", ->
          expect(@view.$el).toContain('a')

        it "anchor contain correct url", ->
          link = @view.$el.find("a").attr("href")
          expect(link).toBe("/download_subtitles?id=#{@html_id}")

      describe "subtitles doesn't exist", ->

        beforeEach ->
          options = $.extend({}, @options, {
            subtitlesExist: false
          })
          @view = new CMS.Views.DownloadSubtitles options

        it "button should not be shown", ->
          expect(@options.$container).not.toContain(@view.$el)
