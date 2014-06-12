describe "DiscussionThreadListView", ->

    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        setFixtures """
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
            <div class="sort-bar"></div>
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
