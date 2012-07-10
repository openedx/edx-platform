describe "CMS.Views.Course", ->
  beforeEach ->
    setFixtures """
      <section id="main-section">
        <section class="main-content"></section>
        <ol id="weeks">
          <li class="cal week-one" style="height: 50px"></li>
          <li class="cal week-two" style="height: 100px"></li>
        </ol>
      </section>
      """
    CMS.unbind()

  describe "render", ->
    beforeEach ->
      spyOn(CMS.Views, "Week").andReturn(jasmine.createSpyObj("Week", ["render"]))
      new CMS.Views.Course(el: $("#main-section")).render()

    it "create week view for each week",->
      expect(CMS.Views.Week.calls[0].args[0])
        .toEqual({ el: $(".week-one").get(0), height: 101 })
      expect(CMS.Views.Week.calls[1].args[0])
        .toEqual({ el: $(".week-two").get(0), height: 101 })

  describe "on content.show", ->
    beforeEach ->
      @view = new CMS.Views.Course(el: $("#main-section"))
      @subView = jasmine.createSpyObj("subView", ["render"])
      @subView.render.andReturn(el: "Subview Content")
      spyOn(@view, "contentHeight").andReturn(100)
      CMS.trigger("content.show", @subView)

    afterEach ->
      $("body").removeClass("content")

    it "add content class to body", ->
      expect($("body").attr("class")).toEqual("content")

    it "replace content in .main-content", ->
      expect($(".main-content")).toHaveHtml("Subview Content")

    it "set height on calendar", ->
      expect($(".cal")).toHaveCss(height: "100px")

    it "set minimum height on all sections", ->
      expect($("#main-section>section")).toHaveCss(minHeight: "100px")

  describe "on content.hide", ->
    beforeEach ->
      $("body").addClass("content")
      @view = new CMS.Views.Course(el: $("#main-section"))
      $(".cal").css(height: 100)
      $("#main-section>section").css(minHeight: 100)
      CMS.trigger("content.hide")

    afterEach ->
      $("body").removeClass("content")

    it "remove content class from body", ->
      expect($("body").attr("class")).toEqual("")

    it "remove content from .main-content", ->
      expect($(".main-content")).toHaveHtml("")

    it "reset height on calendar", ->
      expect($(".cal")).not.toHaveCss(height: "100px")

    it "reset minimum height on all sections", ->
      expect($("#main-section>section")).not.toHaveCss(minHeight: "100px")

  describe "maxWeekHeight", ->
    it "return maximum height of the week element", ->
      @view = new CMS.Views.Course(el: $("#main-section"))
      expect(@view.maxWeekHeight()).toEqual(101)

  describe "contentHeight", ->
    beforeEach ->
      $("body").append($('<header id="test">').height(100).hide())

    afterEach ->
      $("body>header#test").remove()

    it "return the window height minus the header bar", ->
      @view = new CMS.Views.Course(el: $("#main-section"))
      expect(@view.contentHeight()).toEqual($(window).height() - 100)
