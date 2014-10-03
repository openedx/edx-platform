describe 'DiscussionUtil', ->
  beforeEach ->
    DiscussionSpecHelper.setUpGlobals()

  describe "updateWithUndo", ->

    it "calls through to safeAjax with correct params, and reverts the model in case of failure", ->
      deferred = $.Deferred()
      spyOn($, "ajax").andReturn(deferred)
      spyOn(DiscussionUtil, "safeAjax").andCallThrough()

      model = new Backbone.Model({hello: false, number: 42})
      updates = {hello: "world"}

      # the ajax request should fire and the model should be updated
      res = DiscussionUtil.updateWithUndo(model, updates, {foo: "bar"}, "error message")
      expect(DiscussionUtil.safeAjax).toHaveBeenCalled()
      expect(model.attributes).toEqual({hello: "world", number: 42})

      # the error message callback should be set up correctly
      spyOn(DiscussionUtil, "discussionAlert")
      DiscussionUtil.safeAjax.mostRecentCall.args[0].error()
      expect(DiscussionUtil.discussionAlert).toHaveBeenCalledWith("Sorry", "error message")

      # if the ajax call ends in failure, the model state should be reverted
      deferred.reject()
      expect(model.attributes).toEqual({hello: false, number: 42})
