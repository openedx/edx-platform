describe "CMS.Views.Week", ->
  beforeEach ->
    setFixtures """
      <div id="week" data-id="i4x://mitx/course/chapter/week">
        <div class="editable"></div>
        <textarea class="editable-textarea"></textarea>
        <a href="#" class="week-edit" >edit</a>
        <ul class="modules">
          <li id="module-one" class="module"></li>
          <li id="module-two" class="module"></li>
        </ul>
      </div>
      """
    CMS.unbind()

  describe "render", ->
    beforeEach ->
      spyOn(CMS.Views, "Module").andReturn(jasmine.createSpyObj("Module", ["render"]))
      $.fn.inlineEdit = jasmine.createSpy("$.fn.inlineEdit")
      @view = new CMS.Views.Week(el: $("#week"), height: 100).render()

    it "set the height of the element", ->
      expect(@view.el).toHaveCss(height: "100px")

    it "make .editable as inline editor", ->
      expect($.fn.inlineEdit.calls[0].object.get(0))
        .toEqual($(".editable").get(0))

    it "make .editable-test as inline editor", ->
      expect($.fn.inlineEdit.calls[1].object.get(0))
        .toEqual($(".editable-textarea").get(0))

    it "create module subview for each module", ->
      expect(CMS.Views.Module.calls[0].args[0])
        .toEqual({ el: $("#module-one").get(0) })
      expect(CMS.Views.Module.calls[1].args[0])
        .toEqual({ el: $("#module-two").get(0) })

  describe "edit", ->
    beforeEach ->
      new CMS.Views.Week(el: $("#week"), height: 100).render()
      spyOn(CMS, "replaceView")
      spyOn(CMS.Views, "WeekEdit")
        .andReturn(@view = jasmine.createSpy("Views.WeekEdit"))
      $(".week-edit").click()

    it "replace the content with edit week view", ->
      expect(CMS.replaceView).toHaveBeenCalledWith @view
      expect(CMS.Views.WeekEdit).toHaveBeenCalled()

  describe "on content.show", ->
    beforeEach ->
      @view = new CMS.Views.Week(el: $("#week"), height: 100).render()
      @view.$el.height("")
      @view.setHeight()

    it "set the correct height", ->
      expect(@view.el).toHaveCss(height: "100px")

  describe "on content.hide", ->
    beforeEach ->
      @view = new CMS.Views.Week(el: $("#week"), height: 100).render()
      @view.$el.height("100px")
      @view.resetHeight()

    it "remove height from the element", ->
      expect(@view.el).not.toHaveCss(height: "100px")
