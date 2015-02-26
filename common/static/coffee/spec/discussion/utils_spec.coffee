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

  describe 'getHistoryPath', ->
    it "returns pathname as is if no match detected", ->
      expect(DiscussionUtil.getHistoryPath("/some_path", "/other_path")).toEqual("/some_path")
      expect(DiscussionUtil.getHistoryPath("/some/path", "/other_path")).toEqual("/some/path")

    it "removes current history root from start", ->
      expect(DiscussionUtil.getHistoryPath("/some_path", "/")).toEqual("some_path")
      expect(DiscussionUtil.getHistoryPath("/other_path", "/")).toEqual("other_path")
      expect(DiscussionUtil.getHistoryPath("/even/longer/path", "/")).toEqual("even/longer/path")

    it "removes selected thread part if present", ->
      expect(DiscussionUtil.getHistoryPath("/some_path/123/threads/456", "/")).toEqual("some_path")
      expect(DiscussionUtil.getHistoryPath("/some_path/iddqd-idkfa/threads/16def", "/")).toEqual("some_path")
      expect(DiscussionUtil.getHistoryPath("/discussion/i4x-edX-D101-course-T1/threads/54d37d9056c02cc221000005", "/")).toEqual("discussion")
