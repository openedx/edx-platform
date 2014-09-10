describe "DiscussionThreadView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        DiscussionSpecHelper.setUnderscoreFixtures()

        jasmine.Clock.useMock()
        @threadData = DiscussionViewSpecHelper.makeThreadWithProps({})
        @thread = new Thread(@threadData)
        spyOn($, "ajax")
        # Avoid unnecessary boilerplate
        spyOn(DiscussionThreadShowView.prototype, "convertMath")
        spyOn(DiscussionContentView.prototype, "makeWmdEditor")
        spyOn(ThreadResponseView.prototype, "renderShowView")

    renderWithContent = (view, content) ->
        DiscussionViewSpecHelper.setNextResponseContent(content)
        view.render()
        jasmine.Clock.tick(100)

    assertContentVisible = (view, selector, visible) ->
        content = view.$el.find(selector)
        expect(content.length).toBeGreaterThan(0)
        content.each (i, elem) ->
            expect($(elem).is(":visible")).toEqual(visible)

    assertExpandedContentVisible = (view, expanded) ->
        expect(view.$el.hasClass("expanded")).toEqual(expanded)
        assertContentVisible(view, ".post-extended-content", expanded)
        assertContentVisible(view, ".forum-thread-expand", not expanded)
        assertContentVisible(view, ".forum-thread-collapse", expanded)

    assertResponseCountAndPaginationCorrect = (view, countText, displayCountText, buttonText) ->
        expect(view.$el.find(".response-count").text()).toEqual(countText)
        if displayCountText
            expect(view.$el.find(".response-display-count").text()).toEqual(displayCountText)
        else
            expect(view.$el.find(".response-display-count").length).toEqual(0)
        if buttonText
            expect(view.$el.find(".load-response-button").text()).toEqual(buttonText)
        else
            expect(view.$el.find(".load-response-button").length).toEqual(0)

    describe "tab mode", ->
        beforeEach ->
            @view = new DiscussionThreadView({ model: @thread, el: $("#fixture-element"), mode: "tab"})

        describe "response count and pagination", ->
            it "correctly render for a thread with no responses", ->
                renderWithContent(@view, {resp_total: 0, children: []})
                assertResponseCountAndPaginationCorrect(@view, "0 responses", null, null)

            it "correctly render for a thread with one response", ->
                renderWithContent(@view, {resp_total: 1, children: [{}]})
                assertResponseCountAndPaginationCorrect(@view, "1 response", "Showing all responses", null)

            it "correctly render for a thread with one additional page", ->
                renderWithContent(@view, {resp_total: 2, children: [{}]})
                assertResponseCountAndPaginationCorrect(@view, "2 responses", "Showing first response", "Load all responses")

            it "correctly render for a thread with multiple additional pages", ->
                renderWithContent(@view, {resp_total: 111, children: [{}, {}]})
                assertResponseCountAndPaginationCorrect(@view, "111 responses", "Showing first 2 responses", "Load next 100 responses")

            describe "on clicking the load more button", ->
                beforeEach ->
                    renderWithContent(@view, {resp_total: 5, children: [{}]})
                    assertResponseCountAndPaginationCorrect(@view, "5 responses", "Showing first response", "Load all responses")

                it "correctly re-render when all threads have loaded", ->
                    DiscussionViewSpecHelper.setNextResponseContent({resp_total: 5, children: [{}, {}, {}, {}]})
                    @view.$el.find(".load-response-button").click()
                    assertResponseCountAndPaginationCorrect(@view, "5 responses", "Showing all responses", null)

                it "correctly re-render when one page remains", ->
                    DiscussionViewSpecHelper.setNextResponseContent({resp_total: 42, children: [{}, {}]})
                    @view.$el.find(".load-response-button").click()
                    assertResponseCountAndPaginationCorrect(@view, "42 responses", "Showing first 3 responses", "Load all responses")

                it "correctly re-render when multiple pages remain", ->
                    DiscussionViewSpecHelper.setNextResponseContent({resp_total: 111, children: [{}, {}]})
                    @view.$el.find(".load-response-button").click()
                    assertResponseCountAndPaginationCorrect(@view, "111 responses", "Showing first 3 responses", "Load next 100 responses")

    describe "inline mode", ->
        beforeEach ->
            @view = new DiscussionThreadView({ model: @thread, el: $("#fixture-element"), mode: "inline"})

        describe "render", ->
            it "shows content that should be visible when collapsed", ->
                @view.render()
                assertExpandedContentVisible(@view, false)

            it "does not render any responses by default", ->
                @view.render()
                expect($.ajax).not.toHaveBeenCalled()
                expect(@view.$el.find(".responses li").length).toEqual(0)

        describe "expand/collapse", ->
            it "shows/hides appropriate content", ->
                DiscussionViewSpecHelper.setNextResponseContent({resp_total: 0, children: []})
                @view.render()
                @view.expand()
                assertExpandedContentVisible(@view, true)
                @view.collapse()
                assertExpandedContentVisible(@view, false)

            it "switches between the abbreviated and full body", ->
                DiscussionViewSpecHelper.setNextResponseContent({resp_total: 0, children: []})
                longBody = new Array(100).join("test ")
                expectedAbbreviation = DiscussionUtil.abbreviateString(longBody, 140)
                @thread.set("body", longBody)

                @view.render()
                expect($(".post-body").text()).toEqual(expectedAbbreviation)
                expect(DiscussionThreadShowView.prototype.convertMath).toHaveBeenCalled()
                DiscussionThreadShowView.prototype.convertMath.reset()

                @view.expand()
                expect($(".post-body").text()).toEqual(longBody)
                expect(DiscussionThreadShowView.prototype.convertMath).toHaveBeenCalled()
                DiscussionThreadShowView.prototype.convertMath.reset()

                @view.collapse()
                expect($(".post-body").text()).toEqual(expectedAbbreviation)
                expect(DiscussionThreadShowView.prototype.convertMath).toHaveBeenCalled()

            it "strips script tags appropriately", ->
                DiscussionViewSpecHelper.setNextResponseContent({resp_total: 0, children: []})
                longMaliciousBody = new Array(100).join("<script>alert('Until they think warm days will never cease');</script>\n")
                @thread.set("body", longMaliciousBody)
                maliciousAbbreviation = DiscussionUtil.abbreviateString(@thread.get('body'), 140)

                # The nodes' html should be different than the strings, but
                # their texts should be the same, indicating that they've been
                # properly escaped. To be safe, make sure the string "<script"
                # isn't present, either

                @view.render()
                expect($(".post-body").html()).not.toEqual(maliciousAbbreviation)
                expect($(".post-body").text()).toEqual(maliciousAbbreviation)
                expect($(".post-body").html()).not.toContain("<script")

                @view.expand()
                expect($(".post-body").html()).not.toEqual(longMaliciousBody)
                expect($(".post-body").text()).toEqual(longMaliciousBody)
                expect($(".post-body").html()).not.toContain("<script")

                @view.collapse()
                expect($(".post-body").html()).not.toEqual(maliciousAbbreviation)
                expect($(".post-body").text()).toEqual(maliciousAbbreviation)
                expect($(".post-body").html()).not.toContain("<script")

    describe "for question threads", ->
        beforeEach ->
            @thread.set("thread_type", "question")
            @view = new DiscussionThreadView(
                {model: @thread, el: $("#fixture-element"), mode: "tab"}
            )

        renderTestCase = (view, numEndorsed, numNonEndorsed) ->
            generateContent = (idStart, idEnd) ->
                _.map(_.range(idStart, idEnd), (i) -> {"id": "#{i}"})
            renderWithContent(
                view,
                {
                    endorsed_responses: generateContent(0, numEndorsed),
                    non_endorsed_responses: generateContent(numEndorsed, numEndorsed + numNonEndorsed),
                    non_endorsed_resp_total: numNonEndorsed
                }
            )
            expect(view.$(".js-marked-answer-list .discussion-response").length).toEqual(numEndorsed)
            expect(view.$(".js-response-list .discussion-response").length).toEqual(numNonEndorsed)
            assertResponseCountAndPaginationCorrect(
                view,
                "#{numNonEndorsed} #{if numEndorsed then "other " else ""}#{if numNonEndorsed == 1 then "response" else "responses"}",
                if numNonEndorsed then "Showing all responses" else null,
                null
            )

        _.each({"no": 0, "one": 1, "many": 5}, (numEndorsed, endorsedDesc) ->
            _.each({"no": 0, "one": 1, "many": 5}, (numNonEndorsed, nonEndorsedDesc) ->
                it "renders correctly with #{endorsedDesc} marked answer(s) and #{nonEndorsedDesc} response(s)", ->
                    renderTestCase(@view, numEndorsed, numNonEndorsed)
            )
        )

        it "handles pagination correctly", ->
            renderWithContent(
                @view,
                {
                    endorsed_responses: [{id: "1"}, {id: "2"}],
                    non_endorsed_responses: [{id: "3"}, {id: "4"}, {id: "5"}],
                    non_endorsed_resp_total: 42
                }
            )
            DiscussionViewSpecHelper.setNextResponseContent({
                # Add an endorsed response; it should be rendered
                endorsed_responses: [{id: "1"}, {id: "2"}, {id: "6"}],
                non_endorsed_responses: [{id: "7"}, {id: "8"}, {id: "9"}],
                non_endorsed_resp_total: 41
            })
            @view.$el.find(".load-response-button").click()
            expect($(".js-marked-answer-list .discussion-response").length).toEqual(3)
            expect($(".js-response-list .discussion-response").length).toEqual(6)
            assertResponseCountAndPaginationCorrect(
                @view,
                "41 other responses",
                "Showing first 6 responses",
                "Load all responses"
            )
