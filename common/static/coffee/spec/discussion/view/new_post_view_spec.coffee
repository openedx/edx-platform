# -*- coding: utf-8 -*-
describe "NewPostView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        DiscussionSpecHelper.setUnderscoreFixtures()
        window.$$course_id = "edX/999/test"
        spyOn(DiscussionUtil, "makeWmdEditor").andCallFake(
          ($content, $local, cls_identifier) ->
            $local("." + cls_identifier).html("<textarea></textarea>")
        )
        @discussion = new Discussion([], {pages: 1})

    describe "cohort selector", ->
      beforeEach ->
        @course_settings = new DiscussionCourseSettings({
          "category_map": {
            "children": ["Topic"],
            "entries": {"Topic": {"is_cohorted": true, "id": "topic"}}
          },
          "allow_anonymous": false,
          "allow_anonymous_to_peers": false,
          "is_cohorted": true,
          "cohorts": [
            {"id": 1, "name": "Cohort1"},
            {"id": 2, "name": "Cohort2"}
          ]
        })
        @view = new NewPostView(
          el: $("#fixture-element"),
          collection: @discussion,
          course_settings: @course_settings,
          mode: "tab"
        )

      checkVisibility = (view, expectedVisible) =>
        view.render()
        expect(view.$(".js-group-select").is(":visible")).toEqual(expectedVisible)
        if expectedVisible
          expect(view.$(".js-group-select").prop("disabled")).toEqual(false)

      it "is not visible to students", ->
        checkVisibility(@view, false)

      it "allows TAs to see the cohort selector", ->
        DiscussionSpecHelper.makeTA()
        checkVisibility(@view, true)

      it "allows moderators to see the cohort selector", ->
        DiscussionSpecHelper.makeModerator()
        checkVisibility(@view, true)

      it "allows the user to make a cohort selection", ->
        DiscussionSpecHelper.makeModerator()
        @view.render()
        expectedGroupId = null
        DiscussionSpecHelper.makeAjaxSpy(
          (params) -> expect(params.data.group_id).toEqual(expectedGroupId)
        )

        _.each(
          ["1", "2", ""],
          (groupIdStr) =>
            expectedGroupId = groupIdStr
            @view.$(".js-group-select").val(groupIdStr)
            @view.$(".js-post-title").val("dummy title")
            @view.$(".js-post-body textarea").val("dummy body")
            @view.$(".forum-new-post-form").submit()
            expect($.ajax).toHaveBeenCalled()
            $.ajax.reset()
        )

    describe "cancel post resets form ", ->
      beforeEach ->
        @course_settings = new DiscussionCourseSettings({
          "allow_anonymous_to_peers":true,
          "allow_anonymous":true,
          "category_map": {
            "subcategories": {
              "Week 1": {
                "subcategories": {},
                "children": [
                  "Topic-Level Student-Visible Label"
                ],
                "entries": {
                  "Topic-Level Student-Visible Label": {
                    "sort_key": null,
                    "is_cohorted": false,
                    "id": "2b3a858d0c884eb4b272dbbe3f2ffddd"
                  }
                }
              }
            },
            "children": [
              "General",
              "Week 1"
            ],
            "entries": {
              "General": {
                "sort_key": "General",
                "is_cohorted": false,
                "id": "i4x-waqastest-waqastest-course-waqastest"
              }
            }
          }
        })

      checkPostCancelReset = (mode, discussion, course_settings) ->
        view = new NewPostView(
          el: $("#fixture-element"),
          collection: discussion,
          course_settings: course_settings,
          mode: mode
        )
        view.render()
        eventSpy = jasmine.createSpy('eventSpy')
        view.listenTo(view, "newPost:cancel", eventSpy)
        view.$(".post-errors").html("<li class='post-error'>Title can't be empty</li>")
        view.$("label[for$='post-type-discussion']").click()
        view.$(".js-post-title").val("Test Title")
        view.$(".js-post-body textarea").val("Test body")
        view.$(".wmd-preview p").html("Test body")
        view.$(".js-follow").prop("checked", false)
        view.$(".js-anon").prop("checked", true)
        view.$(".js-anon-peers").prop("checked", true)
        if mode == "tab"
          view.$("a[data-discussion-id='2b3a858d0c884eb4b272dbbe3f2ffddd']").click()
        view.$(".cancel").click()
        expect(eventSpy).toHaveBeenCalled()
        expect(view.$(".post-errors").html()).toEqual("");
        if mode == "tab"
          expect($("input[id$='post-type-question']")).toBeChecked()
          expect($("input[id$='post-type-discussion']")).not.toBeChecked()
        expect(view.$(".js-post-title").val()).toEqual("");
        expect(view.$(".js-post-body textarea").val()).toEqual("");
        expect(view.$(".js-follow")).toBeChecked()
        expect(view.$(".js-anon")).not.toBeChecked()
        expect(view.$(".js-anon-peers")).not.toBeChecked()
        if mode == "tab"
          expect(view.$(".js-selected-topic").text()).toEqual("General")

      _.each(["tab", "inline"], (mode) =>
        it "resets the form in #{mode} mode", ->
          checkPostCancelReset(mode, @discussion, @course_settings)
      )

    it "posts to the correct URL", ->
      topicId = "test_topic"
      spyOn($, "ajax").andCallFake(
        (params) ->
          expect(params.url.path()).toEqual(DiscussionUtil.urlFor("create_thread", topicId))
          {always: ->}
      )
      view = new NewPostView(
        el: $("#fixture-element"),
        collection: @discussion,
        course_settings: new DiscussionCourseSettings({
          allow_anonymous: false,
          allow_anonymous_to_peers: false
        }),
        mode: "inline",
        topicId: topicId
      )
      view.render()
      view.$(".forum-new-post-form").submit()
      expect($.ajax).toHaveBeenCalled()
