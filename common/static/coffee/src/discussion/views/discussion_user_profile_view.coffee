if Backbone?
  class @DiscussionUserProfileView extends Backbone.View
#    events:
#      "":""
    initialize: (options) ->
      @renderThreads @$el, @collection
    renderThreads: ($elem, threads) =>
      #Content.loadContentInfos(response.annotated_content_info)
      @discussion = new Discussion()
      @discussion.reset(threads, {silent: false})
      $discussion = $(Mustache.render $("script#_user_profile").html(), {'threads':threads})
      $elem.append($discussion)
      @threadviews = @discussion.map (thread) ->
        new DiscussionThreadProfileView el: @$("article#thread_#{thread.id}"), model: thread
      _.each @threadviews, (dtv) -> dtv.render()

    addThread: (thread, collection, options) =>
      # TODO: When doing pagination, this will need to repaginate. Perhaps just reload page 1?
      article = $("<article class='discussion-thread' id='thread_#{thread.id}'></article>")
      @$('section.discussion > .threads').prepend(article)
      threadView = new DiscussionThreadInlineView el: article, model: thread
      threadView.render()
      @threadviews.unshift threadView
