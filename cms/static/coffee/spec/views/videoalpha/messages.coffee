describe "CMS.Views.SubtitlesMessages", ->
  beforeEach ->
    @prompt = CMS.Views.Prompt
    spy = jasmine.createSpyObj(
      'CMS.Views.Prompt',
      [
        "show",
        "hide"
      ]
    )
    spy['$el'] = $('<div><div id="example"></div></div>')

    CMS.Views.Prompt = () ->
      spy

    spyOn(CMS.Views.SubtitlesMessages.prototype, 'render').andCallThrough()
    @view = new CMS.Views.SubtitlesMessages()

    afterEach ->
      CMS.Views.Prompt = @prompt

  describe "methods", ->
    describe "initialize", ->
      it "default messages are defined", ->
        expect(@view.msg).toBeDefined()

    describe "render", ->
      it "popup to be shown", ->
        @view.render()
        expect(@view.prompt.show).toHaveBeenCalled()

    describe "hide", ->
      it "popup to be shown", ->
        @view.render()
        @view.hide()
        expect(@view.prompt.hide).toHaveBeenCalled()

    describe "findEl", ->
      it "element should be found", ->
        @view.render()
        expect(@view.findEl('#example').length).toBe(1)

