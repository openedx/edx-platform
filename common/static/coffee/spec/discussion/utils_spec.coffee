describe 'DiscussionUtil', ->
  beforeEach ->
    DiscussionSpecHelper.setUpGlobals()

  describe "updateWithUndo", ->

    it "calls through to safeAjax with correct params", ->
      failCallbackSpy = jasmine.createSpy('failCallback')
      spyOn(DiscussionUtil, "safeAjax").andCallFake( ->
        fail: failCallbackSpy
      )
      model = new Backbone.Model({hello: false, number: 42})
      updates = {hello: "world"}
      spyOn(model, "set").andCallThrough()
      res = DiscussionUtil.updateWithUndo(
        model, updates, {foo: "bar"}
      )
      expect(DiscussionUtil.safeAjax).toHaveBeenCalledWith({foo: "bar"})
      expect(model.set).toHaveBeenCalledWith(updates)
      expect(model.attributes).toEqual({hello: "world", number: 42})
      expect(failCallbackSpy).toHaveBeenCalledWith(jasmine.any(Function)) # does not indicate failure, just the setup of a failure callback

    it "calls through to safeAjax with correct params and a custom error", ->
      failCallbackSpy = jasmine.createSpy('failCallback')
      spyOn(DiscussionUtil, "safeAjax").andCallFake( ->
        {fail: failCallbackSpy}
      )
      model = new Backbone.Model({hello: false})
      updates = {hello: "world"}
      spyOn(model, "set").andCallThrough()
      res = DiscussionUtil.updateWithUndo(
        model, updates, {foo: "bar"}, "error message"
      )
      expect(DiscussionUtil.safeAjax).toHaveBeenCalledWith({foo: "bar", error: jasmine.any(Function)})
      expect(model.set).toHaveBeenCalledWith(updates)
      expect(failCallbackSpy).toHaveBeenCalledWith(jasmine.any(Function))

    it "reverts the model after an ajax failure", ->
      deferred = $.Deferred()
      spyOn($, "ajax").andReturn(deferred)
      model = new Backbone.Model({hello: false, number: 42})
      updates = {hello: "world"}
      res = DiscussionUtil.updateWithUndo(model, updates, {foo: "bar"})
      expect(model.attributes).toEqual({hello: "world", number: 42})
      deferred.reject()
      expect(model.attributes).toEqual({hello: false, number: 42})