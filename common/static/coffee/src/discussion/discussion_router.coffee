if Backbone?
  class @DiscussionRouter extends Backbone.Router
    routes:
      "": "allThreads"
      ":forum_name/threads/:thread_id" : "showThread"

    initialize: (options) ->
        @discussion = options['discussion']
        @course_settings = options['course_settings']

        @nav = new DiscussionThreadListView(
            collection: @discussion,
            el: $(".forum-nav"),
            courseSettings: @course_settings
        )
        @nav.on "thread:selected", @navigateToThread
        @nav.on "thread:removed", @navigateToAllThreads
        @nav.on "threads:rendered", @setActiveThread
        @nav.on "thread:created", @navigateToThread
        @nav.render()

        @newPost = $('.new-post-article')
        @newPostView = new NewPostView(
          el: @newPost,
          collection: @discussion,
          course_settings: @course_settings,
          mode: "tab"
        )
        @newPostView.render()
        @listenTo( @newPostView, 'newPost:cancel', @hideNewPost )
        $('.new-post-btn').bind "click", @showNewPost
        $('.new-post-btn').bind "keydown", (event) => DiscussionUtil.activateOnSpace(event, @showNewPost)

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
      unless($(".forum-content").is(":visible"))
        $(".forum-content").fadeIn()
      if(@newPost.is(":visible"))
        @newPost.fadeOut()

      @main = new DiscussionThreadView(el: $(".forum-content"), model: @thread, mode: "tab")
      @main.render()
      @main.on "thread:responses:rendered", =>
        @nav.updateSidebar()

    navigateToThread: (thread_id) =>
      thread = @discussion.get(thread_id)
      @navigate("#{thread.get("commentable_id")}/threads/#{thread_id}", trigger: true)

    navigateToAllThreads: =>
      @navigate("", trigger: true)

    showNewPost: (event) =>
      $('.forum-content').fadeOut(
        duration: 200
        complete: =>
          @newPost.fadeIn(200)
          $('.new-post-title').focus()
      )

    hideNewPost: =>
      @newPost.fadeOut(
        duration: 200
        complete: =>
          $('.forum-content').fadeIn(200)
      )
