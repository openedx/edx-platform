class @DiscussionRouter extends Backbone.Router
  routes:
    "": "allThreads"
    ":forum_name/threads/:thread_id" : "showThread"

  initialize: (options) ->
      @user = options['user']
      @discussion = options['discussion']
      @displayNav()
      @forum = null

  allThreads: ->
      true

  showThread: (forum_name, thread_id) ->
    @forum = forum_name
    thread = @discussion.get(thread_id)
    view = new DiscussionThreadView(el: $(".discussion-column"), model: thread, user: @user)
    view.render()

  displayNav: ->
    view = new DiscussionThreadListView(collection: @discussion, el: $(".post-list"))
    view.on "thread:selected", @navigateToThread
    view.render()

  navigateToThread: (thread_id) =>
    @navigate("#{@forum}/threads/#{thread_id}", trigger: true)
