if Backbone?
  DiscussionApp =
    start: (elem)->
      # TODO: Perhaps eliminate usage of global variables when possible
      DiscussionUtil.loadRolesFromContainer()
      element = $(elem)
      window.$$course_id = element.data("course-id")
      user_info = element.data("user-info")
      sort_preference = element.data("sort-preference")
      threads = element.data("threads")
      thread_pages = element.data("thread-pages")
      content_info = element.data("content-info")
      user = new DiscussionUser(user_info)
      DiscussionUtil.setUser(user)
      window.user = user
      Content.loadContentInfos(content_info)
      discussion = new Discussion(threads, {pages: thread_pages, sort: sort_preference})
      course_settings = new DiscussionCourseSettings(element.data("course-settings"))
      new DiscussionRouter({discussion: discussion, course_settings: course_settings})
      Backbone.history.start({pushState: true, root: "/courses/#{$$course_id}/discussion/forum/"})
  DiscussionProfileApp =
    start: (elem) ->
      # Roles are not included in user profile page, but they are not used for anything
      DiscussionUtil.loadRoles({"Moderator": [], "Administrator": [], "Community TA": []})
      element = $(elem)
      window.$$course_id = element.data("course-id")
      threads = element.data("threads")
      user_info = element.data("user-info")
      window.user = new DiscussionUser(user_info)
      page = element.data("page")
      numPages = element.data("num-pages")
      new DiscussionUserProfileView(el: element, collection: threads, page: page, numPages: numPages)
  $ ->
    $("section.discussion").each (index, elem) ->
      DiscussionApp.start(elem)
    $("section.discussion-user-threads").each (index, elem) ->
      DiscussionProfileApp.start(elem)
