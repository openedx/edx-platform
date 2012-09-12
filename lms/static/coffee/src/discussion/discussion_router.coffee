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
        @newPostView.on "thread:created", @navigateToThread

    allThreads: ->
      @nav.updateSidebar()

    setActiveThread: =>
      if @thread
        @nav.setActiveThread(@thread.get("id"))

    showThread: (forum_name, thread_id) ->
      @thread = @discussion.get(thread_id)
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
      console.log "navigating"
      @navigate("", trigger: true)
