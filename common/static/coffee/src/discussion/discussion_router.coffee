if Backbone?
  class @DiscussionRouter extends Backbone.Router
    routes:
      "": "allThreads"
      ":forum_name/threads/:thread_id" : "showThread"

    initialize: (options) ->
        @discussion = options['discussion']
        @nav = new DiscussionThreadListView(collection: @discussion, el: $(".sidebar"))
        @nav.on "thread:selected", @navigateToThread
        @nav.on "thread:removed", @navigateToAllThreads
        @nav.on "threads:rendered", @setActiveThread
        @nav.render()

        @newPostView = new NewPostView(el: $(".new-post-article"), collection: @discussion)
        @nav.on "thread:created", @navigateToThread
        @newPost = $('.new-post-article')
        $('.new-post-btn').bind "click", @showNewPost
        $('.new-post-cancel').bind "click", @hideNewPost

    allThreads: ->
      @nav.updateSidebar()
      @nav.goHome()

    setActiveThread: =>
      if @thread
        @nav.setActiveThread(@thread.get("id"))
      else
        @nav.goHome

    showThread: (forum_name, thread_id) ->
      @thread = @discussion.get(thread_id)
      @thread.set("unread_comments_count", 0)
      @thread.set("read", true)
      @setActiveThread()
      if(@main)
        @main.cleanup()
        @main.undelegateEvents()

      @main = new DiscussionThreadView(el: $(".discussion-column"), model: @thread)
      @main.render()
      @main.on "thread:responses:rendered", =>
        @nav.updateSidebar()
      @main.on "tag:selected", (tag) =>
        search = "[#{tag}]"
        @nav.setAndSearchFor(search)

    navigateToThread: (thread_id) =>
      thread = @discussion.get(thread_id)
      @navigate("#{thread.get("commentable_id")}/threads/#{thread_id}", trigger: true)

    navigateToAllThreads: =>
      @navigate("", trigger: true)

    showNewPost: (event) =>
      @newPost.slideDown(300)
      $('.new-post-title').focus()

    hideNewPost: (event) =>
      @newPost.slideUp(300)
