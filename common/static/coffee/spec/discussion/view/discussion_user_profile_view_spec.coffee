describe "DiscussionUserProfileView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        setFixtures(
            """
            <script type="text/template" id="_user_profile">
                <section class="discussion">
                    {{#threads}}
                        <article class="discussion-thread" id="thread_{{id}}"/>
                    {{/threads}}
                </section>
                <section class="pagination"/>
            </script>
            <script type="text/template" id="_profile_thread">
                <div class="profile-thread" id="thread_{{id}}"/>
            </script>
            <script type="text/template" id="_pagination">
                <div class="discussion-paginator">
                    <a href="#different-page"/>
                </div>
                <div
                    class="pagination-params"
                    data-leftdots="{{leftdots}}"
                    data-page="{{page}}"
                    data-rightdots="{{rightdots}}"
                >
                    {{#previous}}
                        <div class="previous" data-url="{{url}}" data-number="{{number}}"/>
                    {{/previous}}
                    {{#first}}
                        <div class="first" data-url="{{url}}" data-number="{{number}}"/>
                    {{/first}}
                    {{#lowPages}}
                        <div class="lowPages" data-url="{{url}}" data-number="{{number}}"/>
                    {{/lowPages}}
                    {{#highPages}}
                        <div class="highPages" data-url="{{url}}" data-number="{{number}}"/>
                    {{/highPages}}
                    {{#last}}
                        <div class="last" data-url="{{url}}" data-number="{{number}}"/>
                    {{/last}}
                    {{#next}}
                        <div class="next" data-url="{{url}}" data-number="{{number}}"/>
                    {{/next}}
                </div>
            </script>
            <div class="user-profile-fixture"/>
            """
        )
        spyOn(DiscussionThreadProfileView.prototype, "render")

    makeView = (threads, page, numPages) ->
        return new DiscussionUserProfileView(
            el: $(".user-profile-fixture")
            collection: threads
            page: page
            numPages: numPages
        )

    describe "thread rendering should be correct", ->
        checkRender = (numThreads) ->
            threads = _.map(_.range(numThreads), (i) -> {id: i.toString(), body: "dummy body"})
            view = makeView(threads, 1, 1)
            expect(view.$(".discussion").children().length).toEqual(numThreads)
            _.each(threads, (thread) -> expect(view.$("#thread_#{thread.id}").length).toEqual(1))

        it "with no threads", ->
            checkRender(0)

        it "with one thread", ->
            checkRender(1)

        it "with several threads", ->
            checkRender(5)

    describe "pagination rendering should be correct", ->
        baseUri = URI(window.location)

        pageInfo = (page) -> {url: baseUri.clone().addSearch("page", page).toString(), number: page}

        checkRender = (params) ->
            view = makeView([], params.page, params.numPages)
            paramsQuery = view.$(".pagination-params")
            expect(paramsQuery.length).toEqual(1)
            _.each(
                ["page", "leftdots", "rightdots"],
                (param) ->
                    expect(paramsQuery.data(param)).toEqual(params[param])
            )
            _.each(
                ["previous", "first", "last", "next"],
                (param) ->
                    expected = params[param]
                    expect(paramsQuery.find("." + param).data()).toEqual(
                        if expected then pageInfo(expected) else null
                    )
            )
            _.each(
                ["lowPages", "highPages"]
                (param) ->
                    expect(paramsQuery.find("." + param).map(-> $(this).data()).get()).toEqual(
                        _.map(params[param], pageInfo)
                    )
            )

        it "for one page", ->
            checkRender(
                page: 1
                numPages: 1
                previous: null
                first: null
                leftdots: false
                lowPages: []
                highPages: []
                rightdots: false
                last: null
                next: null
            )

        it "for first page of three (max with no last)", ->
            checkRender(
                page: 1
                numPages: 3
                previous: null
                first: null
                leftdots: false
                lowPages: []
                highPages: [2, 3]
                rightdots: false
                last: null
                next: 2
            )

        it "for first page of four (has last but no dots)", ->
            checkRender(
                page: 1
                numPages: 4
                previous: null
                first: null
                leftdots: false
                lowPages: []
                highPages: [2, 3]
                rightdots: false
                last: 4
                next: 2
            )

        it "for first page of five (has dots)", ->
            checkRender(
                page: 1
                numPages: 5
                previous: null
                first: null
                leftdots: false
                lowPages: []
                highPages: [2, 3]
                rightdots: true
                last: 5
                next: 2
            )

        it "for last page of three (max with no first)", ->
            checkRender(
                page: 3
                numPages: 3
                previous: 2
                first: null
                leftdots: false
                lowPages: [1, 2]
                highPages: []
                rightdots: false
                last: null
                next: null
            )

        it "for last page of four (has first but no dots)", ->
            checkRender(
                page: 4
                numPages: 4
                previous: 3
                first: 1
                leftdots: false
                lowPages: [2, 3]
                highPages: []
                rightdots: false
                last: null
                next: null
            )

        it "for last page of five (has dots)", ->
            checkRender(
                page: 5
                numPages: 5
                previous: 4
                first: 1
                leftdots: true
                lowPages: [3, 4]
                highPages: []
                rightdots: false
                last: null
                next: null
            )

        it "for middle page of five (max with no first/last)", ->
            checkRender(
                page: 3
                numPages: 5
                previous: 2
                first: null
                leftdots: false
                lowPages: [1, 2]
                highPages: [4, 5]
                rightdots: false
                last: null
                next: 4
            )

        it "for middle page of seven (has first/last but no dots)", ->
            checkRender(
                page: 4
                numPages: 7
                previous: 3
                first: 1
                leftdots: false
                lowPages: [2, 3]
                highPages: [5, 6]
                rightdots: false
                last: 7
                next: 5
            )

        it "for middle page of nine (has dots)", ->
            checkRender(
                page: 5
                numPages: 9
                previous: 4
                first: 1
                leftdots: true
                lowPages: [3, 4]
                highPages: [6, 7]
                rightdots: true
                last: 9
                next: 6
            )

    describe "pagination interaction", ->
        beforeEach ->
            @view = makeView([], 1, 1)
            spyOn($, "ajax")

        it "causes updated rendering", ->
            $.ajax.andCallFake(
                (params) =>
                    params.success(
                        discussion_data: [{id: "on_page_42", body: "dummy body"}]
                        page: 42
                        num_pages: 99
                    )
                    {always: ->}
            )
            @view.$(".pagination a").first().click()
            expect(@view.$("#thread_on_page_42").length).toEqual(1)
            expect(@view.$(".pagination-params").data("page")).toEqual(42)
            expect(@view.$(".pagination-params .last").data("number")).toEqual(99)

        it "handles AJAX errors", ->
            spyOn(DiscussionUtil, "discussionAlert")
            $.ajax.andCallFake(
                (params) =>
                    params.error()
                    {always: ->}
            )
            @view.$(".pagination a").first().click()
            expect(DiscussionUtil.discussionAlert).toHaveBeenCalled()
