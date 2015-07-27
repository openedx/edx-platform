class @DiscussionViewSpecHelper
    @makeThreadWithProps = (props) ->
        # Minimal set of properties necessary for rendering
        thread = {
          id: "dummy_id",
          thread_type: "discussion",
          pinned: false,
          endorsed: false,
          votes: {up_count: '0'},
          read: false,
          unread_comments_count: 0,
          comments_count: 0,
          abuse_flaggers: [],
          body: "",
          title: "dummy title",
          created_at: "2014-08-18T01:02:03Z"
        }
        $.extend(thread, props)

    @expectVoteRendered = (view, model, user) ->
        button = view.$el.find(".action-vote")
        expect(button.hasClass("is-checked")).toBe(user.voted(model))
        expect(button.attr("aria-checked")).toEqual(user.voted(model).toString())
        expect(button.find(".vote-count").text()).toMatch("^#{model.get('votes').up_count} Votes?$")
        expect(button.find(".sr.js-sr-vote-count").text()).toMatch("^there are currently #{model.get('votes').up_count} votes?$")

    @checkRenderVote = (view, model) ->
        view.render()
        DiscussionViewSpecHelper.expectVoteRendered(view, model, window.user)
        window.user.vote(model)
        view.render()
        DiscussionViewSpecHelper.expectVoteRendered(view, model, window.user)
        window.user.unvote(model)
        view.render()
        DiscussionViewSpecHelper.expectVoteRendered(view, model, window.user)

    triggerVoteEvent = (view, event, expectedUrl) ->
        deferred = $.Deferred()
        spyOn($, "ajax").andCallFake((params) =>
            expect(params.url.toString()).toEqual(expectedUrl)
            return deferred
        )
        view.render()
        view.$el.find(".action-vote").trigger(event)
        expect($.ajax).toHaveBeenCalled()
        deferred.resolve()

    @checkUpvote = (view, model, user, event) ->
        expect(model.id in user.get('upvoted_ids')).toBe(false)
        initialVoteCount = model.get('votes').up_count
        triggerVoteEvent(view, event, DiscussionUtil.urlFor("upvote_#{model.get('type')}", model.id) + "?ajax=1")
        expect(model.id in user.get('upvoted_ids')).toBe(true)
        expect(model.get('votes').up_count).toEqual(initialVoteCount + 1)

    @checkUnvote = (view, model, user, event) ->
        user.vote(model)
        expect(model.id in user.get('upvoted_ids')).toBe(true)
        initialVoteCount = model.get('votes').up_count
        triggerVoteEvent(view, event, DiscussionUtil.urlFor("undo_vote_for_#{model.get('type')}", model.id) + "?ajax=1")
        expect(user.get('upvoted_ids')).toEqual([])
        expect(model.get('votes').up_count).toEqual(initialVoteCount - 1)

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
        @checkButtonEvents(view, "toggleVote", ".action-vote")

    @setNextResponseContent = (content) ->
        $.ajax.andCallFake(
            (params) =>
                params.success({"content": content})
                {always: ->}
        )
