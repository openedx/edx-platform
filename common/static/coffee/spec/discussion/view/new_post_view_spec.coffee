# -*- coding: utf-8 -*-
describe "NewPostView", ->
    beforeEach ->
        setFixtures(
            """
            <article class="new-post-article" style="display: block;">
                <div class="inner-wrapper">
                    <form class="new-post-form">
                        <div class="left-column" >
                        </div>
                    </form>
                </div>
            </article>

            <script aria-hidden="true" type="text/template" id="new-post-tab-template">
                <div class="inner-wrapper">
                    <form class="new-post-form">
                        <div class="left-column">
                            '<%= topic_dropdown_html %>
                            '<%= options_html %>'
                        </div>
                    </form>
                </div>
            </script>

            <script aria-hidden="true" type="text/template" id="new-post-inline-template">
                <div class="inner-wrapper">
                    <div class="new-post-form-errors">
                    </div>
                    <form class="new-post-form">
                        <%= editor_html %>
                        <%= options_html %>
                    </form>
                </div>
            </script>

            <script aria-hidden="true" type="text/template" id="new-post-menu-entry-template">
                <li role="menuitem"><a href="#" class="topic" data-discussion_id="<%- id %>" aria-describedby="topic-name-span-<%- id %>" cohorted="<%- is_cohorted %>"><%- text %></a></li>
            </script>

            <script aria-hidden="true" type="text/template" id="new-post-menu-category-template">
                <li role="menuitem">
                    <a href="#"><span class="category-menu-span"><%- text %></span></a>
                    <ul role="menu"><%= entries %></ul>
                </li>
            </script>

            <script aria-hidden="true" type="text/template" id="new-post-topic-dropdown-template">
                <span class="topic-dropdown-label" id="topic-dropdown-label">Create new post about:</span>
                <div class="form-topic-drop">
                    <a href="#" aria-labelledby="topic-dropdown-label" class="topic_dropdown_button">${_("Show All Discussions")}<span class="drop-arrow" aria-hidden="true">▾</span></a>
                    <div class="topic_menu_wrapper">
                        <div class="topic_menu_search" role="menu">
                            <label class="sr" for="browse-topic-newpost">Filter List</label>
                            <input type="text" id="browse-topic-newpost" class="form-topic-drop-search-input" placeholder="Filter discussion areas">
                        </div>
                        <ul class="topic_menu" role="menu"><%= topics_html %></ul>
                    </div>
                </div>
            </script>

            <script aria-hidden="true" type="text/template" id="new-post-options-template">
                <div class="options">
                    <input type="checkbox" name="follow" class="discussion-follow" id="new-post-follow" checked><label for="new-post-follow">follow this post</label>
                    <% if (allow_anonymous) { %>
                    <br>
                    <input type="checkbox" name="anonymous" class="discussion-anonymous" id="new-post-anonymous">
                    <label for="new-post-anonymous">post anonymously</label>
                    <% } %>
                    <% if (allow_anonymous_to_peers) { %>
                    <br>
                    <input type="checkbox" name="anonymous_to_peers" class="discussion-anonymous-to-peers" id="new-post-anonymous-to-peers">
                    <label for="new-post-anonymous-to-peers">post anonymously to classmates</label>
                    <% } %>
                    <% if (cohort_options) { %>
                    <div class="form-group-label choose-cohort">
                        ## Translators: This labels the selector for which group of students can view a post
                        Make visible to:
                        <select class="group-filter-select new-post-group" name="group_id">
                            <option value="">All Groups</option>
                            <% _.each(cohort_options, function(opt) { %>
                                <option value="<%= opt.value %>" <% if (opt.selected) { %>selected<% } %>><%- opt.text %></option>
                            <% }); %>
                        </select>
                    </div>
                    <% } %>
                </div>
            </script>

            <script aria-hidden="true" type="text/template" id="new-post-editor-template">
                <div class="form-row">
                    <label class="sr" for="new-post-title">new post title</label>
                    <input type="text" id="new-post-title" class="new-post-title" name="title" placeholder="Title">
                </div>
                <div class="form-row">
                    <div class="new-post-body" name="body" placeholder="Enter your question or comment…"></div>
                </div>
                <input type="submit" id="new-post-submit" class="submit" value="Add post">
                <a href="#" class="new-post-cancel">Cancel</a>
            </script>
            """
        )
        window.$$course_id = "edX/999/test"
        spyOn(DiscussionUtil, "makeWmdEditor")
        @discussion = new Discussion([], {pages: 1})

    describe "Drop down works correct", ->
      beforeEach ->
        @view = new NewPostView(
          el: $(".new-post-article"),
          collection: @discussion,
          course_settings: new DiscussionCourseSettings({
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
          }),
          mode: "tab"
        )
        @view.render()
        @parent_category_text = "Basic Question Types"
        @selected_option_text = "Selection From Options"

      it "completely show parent category and sub-category", ->
        complete_text = @parent_category_text + " / " + @selected_option_text
        selected_text_width = @view.getNameWidth(complete_text)
        @view.maxNameWidth = selected_text_width + 1
        @view.$el.find( "ul.topic_menu li[role='menuitem'] > a" )[1].click()
        dropdown_text = @view.$el.find(".form-topic-drop > a").text()
        expect(complete_text+' ▾').toEqual(dropdown_text)

      it "completely show just sub-category", ->
        complete_text = @parent_category_text + " / " + @selected_option_text
        selected_text_width = @view.getNameWidth(complete_text)
        @view.maxNameWidth = selected_text_width - 10
        @view.$el.find( "ul.topic_menu li[role='menuitem'] > a" )[1].click()
        dropdown_text = @view.$el.find(".form-topic-drop > a").text()
        expect(dropdown_text.indexOf("…")).toEqual(0)
        expect(dropdown_text).toContain(@selected_option_text)

      it "partially show sub-category", ->
        parent_width = @view.getNameWidth(@parent_category_text)
        complete_text = @parent_category_text + " / " + @selected_option_text
        selected_text_width = @view.getNameWidth(complete_text)
        @view.maxNameWidth = selected_text_width - parent_width
        @view.$el.find( "ul.topic_menu li[role='menuitem'] > a" )[1].click()
        dropdown_text = @view.$el.find(".form-topic-drop > a").text()
        expect(dropdown_text.indexOf("…")).toEqual(0)
        expect(dropdown_text.lastIndexOf("…")).toBeGreaterThan(0)

      it "broken span doesn't occur", ->
        complete_text = @parent_category_text + " / " + @selected_option_text
        selected_text_width = @view.getNameWidth(complete_text)
        @view.maxNameWidth = @view.getNameWidth(@selected_option_text) + 100
        @view.$el.find( "ul.topic_menu li[role='menuitem'] > a" )[1].click()
        dropdown_text = @view.$el.find(".form-topic-drop > a").text()
        expect(dropdown_text.indexOf("/ span>")).toEqual(-1)

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
      view.$(".new-post-form").submit()
      expect($.ajax).toHaveBeenCalled()
