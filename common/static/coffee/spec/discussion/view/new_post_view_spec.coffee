# -*- coding: utf-8 -*-
describe "NewPostView", ->
    beforeEach ->
        setFixtures(
            """
            <div class="discussion-body">
                <div class="discussion-column">
                  <article class="new-post-article" style="display: block;"></article>
                </div>
            </div>

            <script aria-hidden="true" type="text/template" id="new-post-template">
                <form class="forum-new-post-form">
                    <% if (mode=="tab") { %>
                    <div class="post-field">
                        <div class="field-label">
                            <span class="field-label-text">
                               Topic Area:
                            </span>
                            <div class="field-input post-topic">
                                <a href="#" class="post-topic-button">
                                    <span class="sr">${_("Discussion topics; current selection is: ")}</span>
                                    <span class="js-selected-topic"></span>
                                    <span class="drop-arrow" aria-hidden="true">▾</span>
                                </a>
                                <div class="topic-menu-wrapper">
                                    <ul class="topic-menu" role="menu"><%= topics_html %></ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    <% } %>
                    <select class="js-group-select">
                      <option value="">All Groups</option>
                      <option value="1">Group 1</option>
                      <option value="2">Group 2</option>
                    </select>
                </form>
            </script>

            <script aria-hidden="true" type="text/template" id="new-post-menu-entry-template">
                <li role="menuitem">
                    <a href="#" class="topic-title" data-discussion-id="<%- id %>" data-cohorted="<%- is_cohorted %>"><%- text %></a>
                </li>
            </script>

            <script aria-hidden="true" type="text/template" id="new-post-menu-category-template">
                <li role="menuitem">
                    <span class="topic-title"><%- text %></span>
                    <ul role="menu" class="topic-submenu"><%= entries %></ul>
                </li>
            </script>
            """
        )
        window.$$course_id = "edX/999/test"
        spyOn(DiscussionUtil, "makeWmdEditor")
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
          "allow_anonymous_to_peers": true
        })
        @view = new NewPostView(
          el: $(".new-post-article"),
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

    it "posts to the correct URL", ->
      topicId = "test_topic"
      spyOn($, "ajax").andCallFake(
        (params) ->
          expect(params.url.path()).toEqual(DiscussionUtil.urlFor("create_thread", topicId))
          {always: ->}
      )
      view = new NewPostView(
        el: $(".new-post-article"),
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
