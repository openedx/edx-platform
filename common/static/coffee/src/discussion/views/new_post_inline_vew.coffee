if Backbone?
  class @NewPostInlineView extends Backbone.View

    initialize: () ->

      @topicId    = @$(".topic").first().data("discussion-id")

      @maxNameWidth = 100

      DiscussionUtil.makeWmdEditor @$el, $.proxy(@$, @), "new-post-body"

      # TODO tags: commenting out til we know what to do with them
      #@$(".new-post-tags").tagsInput DiscussionUtil.tagsInputOptions()

    events:
      "submit .new-post-form":            "createPost"

    # Because we want the behavior that when the body is clicked the menu is
    # closed, we need to ignore clicks in the search field and stop propagation.
    # Without this, clicking the search field would also close the menu.
    ignoreClick: (event) ->
      event.stopPropagation()

    createPost: (event) ->
      event.preventDefault()
      title   = @$(".new-post-title").val()
      body    = @$(".new-post-body").find(".wmd-input").val()
      group = @$(".new-post-group option:selected").attr("value")

      # TODO tags: commenting out til we know what to do with them
      #tags    = @$(".new-post-tags").val()

      anonymous          = false || @$("input.discussion-anonymous").is(":checked")
      anonymous_to_peers = false || @$("input.discussion-anonymous-to-peers").is(":checked")
      follow    = false || @$("input.discussion-follow").is(":checked")

      url = DiscussionUtil.urlFor('create_thread', @topicId)

      DiscussionUtil.safeAjax
        $elem: $(event.target)
        $loading: $(event.target) if event
        url: url
        type: "POST"
        dataType: 'json'
        async: false # TODO when the rest of the stuff below is made to work properly..
        data:
          title: title
          body: body
          group_id: group
          
          # TODO tags: commenting out til we know what to do with them
          #tags: tags
          
          anonymous: anonymous
          anonymous_to_peers: anonymous_to_peers
          auto_subscribe: follow
        error: DiscussionUtil.formErrorHandler(@$(".new-post-form-errors"))
        success: (response, textStatus) =>
          # TODO: Move this out of the callback, this makes it feel sluggish
          thread = new Thread response['content']
          DiscussionUtil.clearFormErrors(@$(".new-post-form-errors"))
          @$el.hide()
          @$(".new-post-title").val("").attr("prev-text", "")
          @$(".new-post-body textarea").val("").attr("prev-text", "")

          # TODO tags, commenting out til we know what to do with them
          #@$(".new-post-tags").val("")
          #@$(".new-post-tags").importTags("")

          @collection.add thread
