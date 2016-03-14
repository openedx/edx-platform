describe "DiscussionUserProfileView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        DiscussionSpecHelper.setUnderscoreFixtures()
        spyOn(DiscussionThreadProfileView.prototype, "render")

    makeThreads = (numThreads) ->
        _.map(_.range(numThreads), (i) -> {id: i.toString(), body: "dummy body"})

    makeView = (threads, page, numPages) ->
        new DiscussionUserProfileView(
            collection: threads
            page: page
            numPages: numPages
        )

    describe "thread rendering should be correct", ->
        checkRender = (numThreads) ->
            threads = makeThreads(numThreads)
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
            paginator = view.$(".discussion-paginator")
            expect(paginator.find(".current-page").text()).toEqual(params["page"].toString())
            expect(paginator.find(".first-page").length).toBe(if params["first"] then 1 else 0);
            expect(paginator.find(".previous-page").length).toBe(if params["previous"] then 1 else 0);
            expect(paginator.find(".previous-ellipses").length).toBe(if params["leftdots"] then 1 else 0);
            expect(paginator.find(".next-page").length).toBe(if params["next"] then 1 else 0);
            expect(paginator.find(".next-ellipses").length).toBe(if params["rightdots"] then 1 else 0);
            expect(paginator.find(".last-page").length).toBe(if params["last"] then 1 else 0);

            get_page_number = (element) => parseInt($(element).text())
            expect(_.map(paginator.find(".lower-page a"), get_page_number)).toEqual(params["lowPages"])
            expect(_.map(paginator.find(".higher-page a"), get_page_number)).toEqual(params["highPages"])

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
            @view = makeView(makeThreads(3), 1, 2)
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
            @view.$(".discussion-pagination a").first().click()
            expect(@view.$(".current-page").text()).toEqual("42")
            expect(@view.$(".last-page").text()).toEqual("99")

        it "handles AJAX errors", ->
            spyOn(DiscussionUtil, "discussionAlert")
            $.ajax.andCallFake(
                (params) =>
                    params.error()
                    {always: ->}
            )
            @view.$(".discussion-pagination a").first().click()
            expect(DiscussionUtil.discussionAlert).toHaveBeenCalled()
