class @DiscussionViewSpecHelper
    @makeThreadWithProps = (props) ->
        # Minimal set of properties necessary for rendering
        thread = {
          id: "dummy_id",
          thread_type: "discussion",
          pinned: false,
          endorsed: false,
          votes: {up_count: '0'},
          unread_comments_count: 0,
          comments_count: 0,
          abuse_flaggers: [],
          body: "",
          created_at: "2014-08-18T01:02:03Z"
        }
        $.extend(thread, props)

    @expectVoteRendered = (view, voted) ->
        button = view.$el.find(".vote-btn")
        if voted
            expect(button.hasClass("is-cast")).toBe(true)
            expect(button.attr("aria-pressed")).toEqual("true")
            expect(button.attr("data-tooltip")).toEqual("remove vote")
            expect(button.text()).toEqual("43 votes (click to remove your vote)")
        else
            expect(button.hasClass("is-cast")).toBe(false)
            expect(button.attr("aria-pressed")).toEqual("false")
            expect(button.attr("data-tooltip")).toEqual("vote")
            expect(button.text()).toEqual("42 votes (click to vote)")

    @checkRenderVote = (view, model) ->
        view.render()
        DiscussionViewSpecHelper.expectVoteRendered(view, false)
        window.user.vote(model)
        view.render()
        DiscussionViewSpecHelper.expectVoteRendered(view, true)
        window.user.unvote(model)
        view.render()
        DiscussionViewSpecHelper.expectVoteRendered(view, false)

    @checkVote = (view, model, modelData, checkRendering) ->
        view.render()
        if checkRendering
            DiscussionViewSpecHelper.expectVoteRendered(view, false)

        spyOn($, "ajax").andCallFake((params) =>
            newModelData = {}
            $.extend(newModelData, modelData, {votes: {up_count: "43"}})
            params.success(newModelData, "success")
            # Caller invokes always function on return value but it doesn't matter here
            {always: ->}
        )

        view.vote()
        expect(window.user.voted(model)).toBe(true)
        if checkRendering
            DiscussionViewSpecHelper.expectVoteRendered(view, true)
        expect($.ajax).toHaveBeenCalled()
        $.ajax.reset()

        # Check idempotence
        view.vote()
        expect(window.user.voted(model)).toBe(true)
        if checkRendering
            DiscussionViewSpecHelper.expectVoteRendered(view, true)
        expect($.ajax).toHaveBeenCalled()

    @checkUnvote = (view, model, modelData, checkRendering) ->
        window.user.vote(model)
        expect(window.user.voted(model)).toBe(true)
        if checkRendering
            DiscussionViewSpecHelper.expectVoteRendered(view, true)

        spyOn($, "ajax").andCallFake((params) =>
            newModelData = {}
            $.extend(newModelData, modelData, {votes: {up_count: "42"}})
            params.success(newModelData, "success")
            # Caller invokes always function on return value but it doesn't matter here
            {always: ->}
        )

        view.unvote()
        expect(window.user.voted(model)).toBe(false)
        if checkRendering
            DiscussionViewSpecHelper.expectVoteRendered(view, false)
        expect($.ajax).toHaveBeenCalled()
        $.ajax.reset()

        # Check idempotence
        view.unvote()
        expect(window.user.voted(model)).toBe(false)
        if checkRendering
            DiscussionViewSpecHelper.expectVoteRendered(view, false)
        expect($.ajax).toHaveBeenCalled()

    @checkToggleVote = (view, model) ->
        event = {preventDefault: ->}
        spyOn(event, "preventDefault")
        spyOn(view, "vote").andCallFake(() -> window.user.vote(model))
        spyOn(view, "unvote").andCallFake(() -> window.user.unvote(model))

        expect(window.user.voted(model)).toBe(false)
        view.toggleVote(event)
        expect(view.vote).toHaveBeenCalled()
        expect(view.unvote).not.toHaveBeenCalled()
        expect(event.preventDefault.callCount).toEqual(1)

        view.vote.reset()
        view.unvote.reset()
        expect(window.user.voted(model)).toBe(true)
        view.toggleVote(event)
        expect(view.vote).not.toHaveBeenCalled()
        expect(view.unvote).toHaveBeenCalled()
        expect(event.preventDefault.callCount).toEqual(2)

    @checkButtonEvents = (view, viewFunc, buttonSelector) ->
        spy = spyOn(view, viewFunc)
        button = view.$el.find(buttonSelector)

        button.click()
        expect(spy).toHaveBeenCalled()
        spy.reset()
        button.trigger($.Event("keydown", {which: 13}))
        expect(spy).not.toHaveBeenCalled()
        spy.reset()
        button.trigger($.Event("keydown", {which: 32}))
        expect(spy).toHaveBeenCalled()
        
    @checkVoteButtonEvents = (view) ->
        @checkButtonEvents(view, "toggleVote", ".vote-btn")

    @setNextResponseContent = (content) ->
        $.ajax.andCallFake(
            (params) =>
                params.success({"content": content})
                {always: ->}
        )
