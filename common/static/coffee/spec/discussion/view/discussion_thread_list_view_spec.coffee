describe "DiscussionThreadListView", ->

    beforeEach ->

        setFixtures """
        <script type="text/template" id="thread-list-item-template">
          <a href="<%- id %>" data-id="<%- id %>">
            <span class="title"><%- title %></span>
            <span class="comments-count">
                <%
            var fmt;
            var data = {
                'span_sr_open': '<span class="sr">',
                'span_close': '</span>',
                'unread_comments_count': unread_comments_count,
                'comments_count': comments_count
                };
            if (unread_comments_count > 0) {
                fmt = '%(comments_count)s %(span_sr_open)scomments (%(unread_comments_count)s unread comments)%(span_close)s';
            } else {
                fmt = '%(comments_count)s %(span_sr_open)scomments %(span_close)s';
            }
            print(interpolate(fmt, data, true));
            %>
            </span>

            <span class="votes-count">+<%=
                interpolate(
                    '%(votes_up_count)s%(span_sr_open)s votes %(span_close)s',
                    {'span_sr_open': '<span class="sr">', 'span_close': '</span>', 'votes_up_count': votes['up_count']},
                    true
                    )
            %></span>
          </a>
        </script>
        <script type="text/template" id="thread-list-template">
            <div class="browse-search">
                <div class="home"></div>
                <div class="browse is-open"></div>
                <div class="search">
                    <form class="post-search">
                        <label class="sr" for="search-discussions">Search</label>
                        <input type="text" id="search-discussions" placeholder="Search all discussions" class="post-search-field">
                    </form>
                </div>
            </div>
            <div class="sort-bar">
              <span class="sort-label" id="sort-label">Sort by:</span>
              <ul role="radiogroup" aria-labelledby="sort-label">
                  <li><a href="#" role="radio" aria-checked="false" data-sort="date">date</a></li>
                  <li><a href="#" role="radio" aria-checked="false" data-sort="votes">votes</a></li>
                  <li><a href="#" role="radio" aria-checked="false" data-sort="comments">comments</a></li>
              </ul>
            </div>
            <div class="search-alerts"></div>
            <div class="post-list-wrapper">
                <ul class="post-list"></ul>
            </div>
        </script>
        <script aria-hidden="true" type="text/template" id="search-alert-template">
            <div class="search-alert" id="search-alert-<%- cid %>">
                <div class="search-alert-content">
                  <p class="message"><%- message %></p>
                </div>

                <div class="search-alert-controls">
                  <a href="#" class="dismiss control control-dismiss"><i class="icon icon-remove"></i></a>
                </div>
            </div>
        </script>
        <div class="sidebar"></div>
        """
        @threads = [
          {id: "1", title: "Thread1", body: "dummy body", votes: {up_count: '20'}, unread_comments_count:0, comments_count:1, created_at: '2013-04-03T20:08:39Z',},
          {id: "2", title: "Thread2", body: "dummy body", votes: {up_count: '42'}, unread_comments_count:0, comments_count:2, created_at: '2013-04-03T20:07:39Z',},
          {id: "3", title: "Thread3", body: "dummy body", votes: {up_count: '12'}, unread_comments_count:0, comments_count:3, created_at: '2013-04-03T20:06:39Z',},
        ]
        window.$$course_id = "TestOrg/TestCourse/TestRun"
        window.user = new DiscussionUser({id: "567", upvoted_ids: []})

        spyOn($, "ajax")

        @discussion = new Discussion([])
        @view = new DiscussionThreadListView({collection: @discussion, el: $(".sidebar")})
        @view.render()

    testAlertMessages = (expectedMessages) ->
        expect($(".search-alert .message").map( ->
          $(@).html()
        ).get()).toEqual(expectedMessages)

    it "renders and removes search alerts", ->
        testAlertMessages []
        foo = @view.addSearchAlert("foo")
        testAlertMessages ["foo"]
        bar = @view.addSearchAlert("bar")
        testAlertMessages ["foo", "bar"]
        @view.removeSearchAlert(foo.cid)
        testAlertMessages ["bar"]
        @view.removeSearchAlert(bar.cid)
        testAlertMessages []

    it "clears all search alerts", ->
        @view.addSearchAlert("foo")
        @view.addSearchAlert("bar")
        @view.addSearchAlert("baz")
        testAlertMessages ["foo", "bar", "baz"]
        @view.clearSearchAlerts()
        testAlertMessages []

    testCorrection = (view, correctedText) ->
        spyOn(view, "addSearchAlert")
        $.ajax.andCallFake(
            (params) =>
                params.success(
                    {discussion_data: [], page: 42, num_pages: 99, corrected_text: correctedText}, 'success'
                )
                {always: ->}
        )
        view.searchFor("dummy")
        expect($.ajax).toHaveBeenCalled()

    it "adds a search alert when an alternate term was searched", ->
        testCorrection(@view, "foo")
        expect(@view.addSearchAlert).toHaveBeenCalled()
        expect(@view.addSearchAlert.mostRecentCall.args[0]).toMatch(/foo/)

    it "does not add a search alert when no alternate term was searched", ->
        testCorrection(@view, null)
        expect(@view.addSearchAlert).not.toHaveBeenCalled()

    it "clears search alerts when a new search is performed", ->
        spyOn(@view, "clearSearchAlerts")
        spyOn(DiscussionUtil, "safeAjax")
        @view.searchFor("dummy")
        expect(@view.clearSearchAlerts).toHaveBeenCalled()

    it "clears search alerts when the underlying collection changes", ->
        spyOn(@view, "clearSearchAlerts")
        spyOn(@view, "renderThread")
        @view.collection.trigger("change", new Thread({id: 1}))
        expect(@view.clearSearchAlerts).toHaveBeenCalled()

    makeView = (discussion) ->
      return new DiscussionThreadListView(
          el: $(".sidebar"),
          collection: discussion
      )

    checkThreadsOrdering =  (view, sort_order, type) ->
      expect(view.$el.find(".post-list .list-item").children().length).toEqual(3)
      expect(view.$el.find(".post-list .list-item:nth-child(1) .title").text()).toEqual(sort_order[0])
      expect(view.$el.find(".post-list .list-item:nth-child(2) .title").text()).toEqual(sort_order[1])
      expect(view.$el.find(".post-list .list-item:nth-child(3) .title").text()).toEqual(sort_order[2])
      expect(view.$el.find(".sort-bar a.active").text()).toEqual(type)

    describe "thread rendering should be correct", ->
        checkRender = (threads, type, sort_order) ->
            discussion = new Discussion(threads, {pages: 1, sort: type})
            view = makeView(discussion)
            view.render()
            checkThreadsOrdering(view, sort_order, type)

        it "with sort preference date", ->
            checkRender(@threads, "date", [ "Thread1", "Thread2", "Thread3"])

        it "with sort preference votes", ->
            checkRender(@threads, "votes", [ "Thread2", "Thread1", "Thread3"])

        it "with sort preference comments", ->
            checkRender(@threads, "comments", [ "Thread3", "Thread2", "Thread1"])

    describe "Sort click should be correct", ->
      changeSorting = (threads, selected_type, new_type, sort_order) ->
        discussion = new Discussion(threads, {pages: 1, sort: selected_type})
        view = makeView(discussion)
        view.render()
        expect(view.$el.find(".sort-bar a.active").text()).toEqual(selected_type)
        sorted_threads = []
        if new_type == 'date'
          sorted_threads = [threads[0], threads[1], threads[2]]
        else if new_type == 'comments'
          sorted_threads = [threads[2], threads[1], threads[0]]
        else if new_type == 'votes'
          sorted_threads = [threads[1], threads[0], threads[2]]
        $.ajax.andCallFake((params) =>
          params.success(
                {"discussion_data":sorted_threads, page:1, num_pages:1}
          )
          {always: ->}
        )
        view.$el.find(".sort-bar a[data-sort='"+new_type+"']").click()
        expect($.ajax).toHaveBeenCalled()
        expect(view.sortBy).toEqual(new_type)
        checkThreadsOrdering(view, sort_order, new_type)

      it "with sort preference date", ->
          changeSorting(@threads, "comments", "date", ["Thread1", "Thread2", "Thread3"])

      it "with sort preference votes", ->
          changeSorting(@threads, "date", "votes", ["Thread2", "Thread1", "Thread3"])

      it "with sort preference comments", ->
          changeSorting(@threads, "votes", "comments", ["Thread3", "Thread2", "Thread1"])
