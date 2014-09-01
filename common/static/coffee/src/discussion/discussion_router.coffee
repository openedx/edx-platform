if Backbone?
  class @DiscussionRouter extends Backbone.Router
    initialize: (options) ->
        @allThreadsRoute = DiscussionUtil.route_prefix
        @singleThreadRoute = @getSingleThreadRoute(":forum_name", ":thread_id")

        @route(@allThreadsRoute, "allThreads")
        @route(@singleThreadRoute, "showThread")

        @discussion = options['discussion']
        @course_settings = options['course_settings']

        @nav = new DiscussionThreadListView(
            collection: @discussion,
            el: $(".forum-nav"),
            courseSettings: @course_settings
        )
        @nav.on "thread:selected", @navigateToThread
        @nav.on "thread:deselected", @navigateToAllThreads
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

    getSingleThreadRoute: (commentable_id, thread_id) ->
      base_route = "#{commentable_id}/threads/#{thread_id}"
      if DiscussionUtil.route_prefix
        base_route = "#{DiscussionUtil.route_prefix}/#{base_route}"
      base_route

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
      if !@thread
        callback = (thread) =>
          @thread = thread
          @renderThreadView()
        @retrieveSingleThread(forum_name, thread_id, callback)
      else
        @renderThreadView()

    renderThreadView: () ->
      @thread.set("unread_comments_count", 0)
      @thread.set("read", true)
      @setActiveThread()
      @showMain()

    showMain: =>
      if(@main)
        @main.cleanup()
        @main.undelegateEvents()
      unless($(".forum-content").is(":visible"))
        $(".forum-content").fadeIn()
      if(@newPost.is(":visible"))
        @newPost.fadeOut()

      @main = new DiscussionThreadView(
        el: $(".forum-content"),

        model: @thread,
        mode: "tab",
        course_settings: @course_settings,
      )
      @main.render()
      @main.on "thread:responses:rendered", =>
        @nav.updateSidebar()
      @thread.on "thread:thread_type_updated", @showMain

    navigateToThread: (thread_id) =>
      thread = @discussion.get(thread_id)
      @navigate(@getSingleThreadRoute(thread.get("commentable_id"), thread_id), trigger: true)

    navigateToAllThreads: =>
      @navigate(@allThreadsRoute, trigger: true)

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
