class @DiscussionRouter extends Backbone.Router
  routes:
    "": "allThreads"
    ":forum_name/threads/:thread_id" : "showThread"

  initialize: (options) ->
      @discussion = options['discussion']
      @nav = new DiscussionThreadListView(collection: @discussion, el: $(".sidebar"))
      @nav.on "thread:selected", @navigateToThread
      @nav.on "threads:rendered", @setActiveThread
      @nav.render()

  allThreads: ->
      true

  setActiveThread: =>
    if @thread
      @nav.setActiveThread(@thread.get("id"))

  showThread: (forum_name, thread_id) ->
    @thread = @discussion.get(thread_id)
    @setActiveThread()
    if(@main)
      @main.undelegateEvents()

    @main = new DiscussionThreadView(el: $(".discussion-column"), model: @thread)
    @main.render()

  navigateToThread: (thread_id) =>
    thread = @discussion.get(thread_id)
    @navigate("#{thread.get("commentable_id")}/threads/#{thread_id}", trigger: true)
