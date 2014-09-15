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

    describe "Drop down works correct", ->
      beforeEach ->
        @course_settings = new DiscussionCourseSettings({
          "category_map": {
            "subcategories": {
              "Basic Question Types": {
                "subcategories": {},
                "children": ["Selection From Options"],
                "entries": {
                  "Selection From Options": {
                    "sort_key": null,
                    "is_cohorted": true,
                    "id": "cba3e4cd91d0466b9ac50926e495b76f"
                  }
                },
              },
            },
            "children": ["Basic Question Types"],
            "entries": {}
          },
          "allow_anonymous": true,
          "allow_anonymous_to_peers": true,
          "is_cohorted": true
        })
        @view = new NewPostView(
          el: $("#fixture-element"),
          collection: @discussion,
          course_settings: @course_settings,
          mode: "tab"
        )
        @view.render()
        @parent_category_text = "Basic Question Types"
        @selected_option_text = "Selection From Options"

      it "completely show parent category and sub-category", ->
        complete_text = @parent_category_text + " / " + @selected_option_text
        selected_text_width = @view.getNameWidth(complete_text)
        @view.maxNameWidth = selected_text_width + 1
        @view.$el.find( "a.topic-title" ).first().click()
        dropdown_text = @view.$el.find(".js-selected-topic").text()
        expect(complete_text).toEqual(dropdown_text)

      it "completely show just sub-category", ->
        complete_text = @parent_category_text + " / " + @selected_option_text
        selected_text_width = @view.getNameWidth(complete_text)
        @view.maxNameWidth = selected_text_width - 10
        @view.$el.find( "a.topic-title" ).first().click()
        dropdown_text = @view.$el.find(".js-selected-topic").text()
        expect(dropdown_text.indexOf("…")).toEqual(0)
        expect(dropdown_text).toContain(@selected_option_text)

      it "partially show sub-category", ->
        parent_width = @view.getNameWidth(@parent_category_text)
        complete_text = @parent_category_text + " / " + @selected_option_text
        selected_text_width = @view.getNameWidth(complete_text)
        @view.maxNameWidth = selected_text_width - parent_width
        @view.$el.find( "a.topic-title" ).first().click()
        dropdown_text = @view.$el.find(".js-selected-topic").text()
        expect(dropdown_text.indexOf("…")).toEqual(0)
        expect(dropdown_text.lastIndexOf("…")).toBeGreaterThan(0)

      it "broken span doesn't occur", ->
        complete_text = @parent_category_text + " / " + @selected_option_text
        selected_text_width = @view.getNameWidth(complete_text)
        @view.maxNameWidth = @view.getNameWidth(@selected_option_text) + 100
        @view.$el.find( "a.topic-title" ).first().click()
        dropdown_text = @view.$el.find(".js-selected-topic").text()
        expect(dropdown_text.indexOf("/ span>")).toEqual(-1)

      describe "cohort selector", ->
        renderWithCohortedTopics = (course_settings, view, isCohortedFirst) ->
          course_settings.set(
            "category_map",
            {
              "children": if isCohortedFirst then ["Cohorted", "Non-Cohorted"] else ["Non-Cohorted", "Cohorted"],
              "entries": {
                "Non-Cohorted": {
                  "sort_key": null,
                  "is_cohorted": false,
                  "id": "non-cohorted"
                },
                "Cohorted": {
                  "sort_key": null,
                  "is_cohorted": true,
                  "id": "cohorted"
                }
              }
            }
          )
          DiscussionSpecHelper.makeModerator()
          view.render()

        expectCohortSelectorEnabled = (view, enabled) ->
          expect(view.$(".js-group-select").prop("disabled")).toEqual(not enabled)
          if not enabled
            expect(view.$(".js-group-select option:selected").attr("value")).toEqual("")

        it "is disabled with non-cohorted default topic and enabled by selecting cohorted topic", ->
          renderWithCohortedTopics(@course_settings, @view, false)
          expectCohortSelectorEnabled(@view, false)
          @view.$("a.topic-title[data-discussion-id=cohorted]").click()
          expectCohortSelectorEnabled(@view, true)

        it "is enabled with cohorted default topic and disabled by selecting non-cohorted topic", ->
          renderWithCohortedTopics(@course_settings, @view, true)
          expectCohortSelectorEnabled(@view, true)
          @view.$("a.topic-title[data-discussion-id=non-cohorted]").click()
          expectCohortSelectorEnabled(@view, false)

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
        view.$("#tab-post-type-discussion").click()
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
        expect($("##{mode}-post-type-question").prop("checked")).toBe(true)
        expect($("##{mode}-post-type-discussion").prop("checked")).toBe(false)
        expect(view.$(".js-post-title").val()).toEqual("");
        expect(view.$(".js-post-body textarea").val()).toEqual("");
        expect(view.$(".js-follow").prop("checked")).toBe(true)
        expect(view.$(".js-anon").prop("checked")).toBe(false)
        expect(view.$(".js-anon-peers").prop("checked")).toBe(false)
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
