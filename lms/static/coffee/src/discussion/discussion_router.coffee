class @DiscussionRouter extends Backbone.Router
  routes:
    "": "allThreads"
    ":forum_name/threads/:thread_id" : "showThread"

  initialize: (options) ->
      @discussion = options['discussion']
      @nav = new DiscussionThreadListView(collection: @discussion, el: $(".sidebar"))
      @nav.on "thread:selected", @navigateToThread
      @nav.render()
      @main = new DiscussionThreadView(el: $(".discussion-column"))

  allThreads: ->
      true

  showThread: (forum_name, thread_id) ->
    @nav.setActiveThread(thread_id)
    thread = @discussion.get(thread_id)
    @main.model = thread
    @main.render()

  navigateToThread: (thread_id) =>
    thread = @discussion.get(thread_id)
    @navigate("#{thread.get("commentable_id")}/threads/#{thread_id}", trigger: true)
