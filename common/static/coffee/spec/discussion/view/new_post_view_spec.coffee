# -*- coding: utf-8 -*-
describe "NewPostView", ->
    beforeEach ->
        setFixtures(
            """
                    <article class="new-post-article" style="display: block;">
                    <div class="inner-wrapper">
                        <form class="new-post-form">
                            <div class="left-column" >
                                <span class="topic-dropdown-label" id="topic-dropdown-label">Create new post about:</span>

                                <div class="form-topic-drop">
                                    <a href="#" aria-labelledby="topic-dropdown-label" class="topic_dropdown_button">… / TA Feedba …
                                        <span class="drop-arrow">▾</span></a>

                                    <div class="topic_menu_wrapper">
                                        <div class="topic_menu_search" role="menu">
                                            <label class="sr" for="browse-topic-newpost">Filter List</label>
                                            <input type="text" id="browse-topic-newpost" class="form-topic-drop-search-input"
                                                   placeholder="Filter discussion areas">
                                        </div>
                                        <ul class="topic_menu" role="menu">
                                            <li role="menuitem">
                                                <a href="#"><span class="category-menu-span">Basic Question Types</span></a>
                                                <ul role="menu">
                                                    <li role="menuitem"><a href="#" class="topic"
                                                                           data-discussion_id="a22e81688d154e059f9a2012a26b27af"
                                                                           aria-describedby="topic-name-span-a22e81688d154e059f9a2012a26b27af"
                                                                           cohorted="False">Selection from Options</a></li>
                                                </ul>
                                            </li>
                                        </ul>
                                    </div>
                                </div>
                                <div class="options">
                                    <input type="checkbox" name="follow" class="discussion-follow" id="new-post-follow"
                                           checked=""><label for="new-post-follow">follow this post</label>
                                    <br>
                                    <input type="checkbox" name="anonymous" class="discussion-anonymous" id="new-post-anonymous"><label
                                        for="new-post-anonymous">post anonymously</label>
                                </div>
                            </div>
                        </form>
                    </div>
                </article>
            """
        )
        window.$$course_id = "edX/999/test"
        spyOn(DiscussionUtil, "makeWmdEditor")
        @discussion = new Discussion([], {pages: 1})
        @view = new NewPostView(
          el: $(".new-post-article"),
          collection: @discussion,
        )
        @parent_category_text = @view.$el.find( "ul.topic_menu li[role='menuitem'] > a" )[0].text
        @selected_option_text = @view.$el.find( "ul.topic_menu li[role='menuitem'] > a" )[1].text

    makeView = (discussion) ->
        spyOn(DiscussionUtil, "makeWmdEditor")
        return new NewPostView(
          el: $(".new-post-article"),
          collection: discussion,
        )

    describe "Drop down works correct", ->

      it "broken span doesn't occur", ->
        complete_text = @parent_category_text + " / " + @selected_option_text
        selected_text_width = @view.getNameWidth(complete_text)
        @view.maxNameWidth = @view.getNameWidth(@selected_option_text) + 100
        @view.$el.find( "ul.topic_menu li[role='menuitem'] > a" )[1].click()
        dropdown_text = @view.$el.find(".form-topic-drop > a").text()
        expect(dropdown_text.indexOf("/ span>")).toEqual(-1)

