if Backbone?
  class @DiscussionModuleView extends Backbone.View
    events:
      "click .discussion-show": "toggleDiscussion"
      "click .new-post-btn": "toggleNewPost"
      "click .new-post-cancel": "hideNewPost"
    initialize: ->

    toggleNewPost: (event) ->
      if @newPostForm.is(':hidden')
        @newPostForm.slideDown(300)
      else
        @newPostForm.slideUp(300)
    hideNewPost: (event) ->
      @newPostForm.slideUp(300)

    toggleDiscussion: (event) ->
      console.log "doing stuff yo"
      if @showed
        @$("section.discussion").hide()
        $(event.target).html("Show Discussion")
        @showed = false
      else
        if @retrieved
          @$("section.discussion").show()
          $(event.target).html("Hide Discussion")
          @showed = true
        else
          $elem = $(event.target)
          discussion_id = $elem.attr("discussion_id")
          url = DiscussionUtil.urlFor 'retrieve_discussion', discussion_id
          DiscussionUtil.safeAjax
            $elem: $elem
            $loading: $elem
            url: url
            type: "GET"
            dataType: 'json'
            success: (response, textStatus, jqXHR) => @createDiscussion(event, response, textStatus)

    createDiscussion: (event, response, textStatus) =>
      console.log "HI"
      console.log response
      window.user = new DiscussionUser(response.user_info)
      Content.loadContentInfos(response.annotated_content_info)
      console.log "infod"
      $(event.target).html("Hide Discussion")
      discussion = new Discussion()
      discussion.reset(response.discussion_data, {silent: false})
      $discussion = $(Mustache.render $("script#_inline_discussion").html(), {'threads':response.discussion_data})
      $(".discussion-module").append($discussion)
      @newPostForm = $('.new-post-article')
      discussion.each (thread) ->
        element = $("article#thread_#{thread.id}")
        dtv = new DiscussionThreadInlineView el: element, model: thread
        dtv.render()
      DiscussionUtil.bulkUpdateContentInfo(window.$$annotated_content_info)
      @newPostView = new NewPostInlineView el: $('.new-post-article'), collection: discussion
      @retrieved = true
      @showed = true
