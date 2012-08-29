class @DiscussionRouter extends Backbone.Router
  routes:
    "": "allThreads"
    ":forum_name/threads/:thread_id" : "showThread"

  initialize: (options) ->
      @user = options['user']
      @discussion = options['discussion']
      @nav = new DiscussionThreadListView(collection: @discussion, el: $(".post-list"))
      @nav.on "thread:selected", @navigateToThread
      @nav.render()

  allThreads: ->
      true

  showThread: (forum_name, thread_id) ->
    @nav.setActiveThread(thread_id)
    thread = @discussion.get(thread_id)
    view = new DiscussionThreadView(el: $(".discussion-column"), model: thread, user: @user)
    view.render()

  navigateToThread: (thread_id) =>
    thread = @discussion.get(thread_id)
    @navigate("#{thread.get("commentable_id")}/threads/#{thread_id}", trigger: true)
