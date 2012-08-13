describe "CMS", ->
  beforeEach ->
    CMS.unbind()

  it "should initialize Models", ->
    expect(CMS.Models).toBeDefined()

  it "should initialize Views", ->
    expect(CMS.Views).toBeDefined()

  describe "start", ->
    beforeEach ->
      @element = $("<div>")
      spyOn(CMS.Views, "Course").andReturn(jasmine.createSpyObj("Course", ["render"]))
      CMS.start(@element)

    it "create the Course", ->
      expect(CMS.Views.Course).toHaveBeenCalledWith(el: @element)
      expect(CMS.Views.Course().render).toHaveBeenCalled()

  describe "view stack", ->
    beforeEach ->
      @currentView = jasmine.createSpy("currentView")
      CMS.viewStack = [@currentView]

    describe "replaceView", ->
      beforeEach ->
        @newView = jasmine.createSpy("newView")
        CMS.on("content.show", (@expectedView) =>)
        CMS.replaceView(@newView)

      it "replace the views on the viewStack", ->
        expect(CMS.viewStack).toEqual([@newView])

      it "trigger content.show on CMS", ->
        expect(@expectedView).toEqual(@newView)

    describe "pushView", ->
      beforeEach ->
        @newView = jasmine.createSpy("newView")
        CMS.on("content.show", (@expectedView) =>)
        CMS.pushView(@newView)

      it "push new view onto viewStack", ->
        expect(CMS.viewStack).toEqual([@currentView, @newView])

      it "trigger content.show on CMS", ->
        expect(@expectedView).toEqual(@newView)

    describe "popView", ->
      it "remove the current view from the viewStack", ->
        CMS.popView()
        expect(CMS.viewStack).toEqual([])

      describe "when there's no view on the viewStack", ->
        beforeEach ->
          CMS.viewStack = [@currentView]
          CMS.on("content.hide", => @eventTriggered = true)
          CMS.popView()

        it "trigger content.hide on CMS", ->
          expect(@eventTriggered).toBeTruthy

      describe "when there's previous view on the viewStack", ->
        beforeEach ->
          @parentView = jasmine.createSpyObj("parentView", ["delegateEvents"])
          CMS.viewStack = [@parentView, @currentView]
          CMS.on("content.show", (@expectedView) =>)
          CMS.popView()

        it "trigger content.show with the previous view on CMS", ->
          expect(@expectedView).toEqual @parentView

        it "re-bind events on the view", ->
          expect(@parentView.delegateEvents).toHaveBeenCalled()

describe "main helper", ->
  beforeEach ->
    @previousAjaxSettings = $.extend(true, {}, $.ajaxSettings)
    window.stubCookies["csrftoken"] = "stubCSRFToken"
    $(document).ready()

  afterEach ->
    $.ajaxSettings = @previousAjaxSettings

  it "turn on Backbone emulateHTTP", ->
    expect(Backbone.emulateHTTP).toBeTruthy()

  it "setup AJAX CSRF token", ->
    expect($.ajaxSettings.headers["X-CSRFToken"]).toEqual("stubCSRFToken")
