if Backbone?
  class @DiscussionModuleView extends Backbone.View
    events:
      "click .discussion-show": "toggleDiscussion"
      "keydown .discussion-show":
        (event) -> DiscussionUtil.activateOnSpace(event, @toggleDiscussion)
      "click .new-post-btn": "toggleNewPost"
      "keydown .new-post-btn":
        (event) -> DiscussionUtil.activateOnSpace(event, @toggleNewPost)
      "click .new-post-cancel": "hideNewPost"
      "click .discussion-paginator a": "navigateToPage"

    paginationTemplate: -> DiscussionUtil.getTemplate("_pagination")
    page_re: /\?discussion_page=(\d+)/
    initialize: ->
      @toggleDiscussionBtn = @$(".discussion-show")
      # Set the page if it was set in the URL. This is used to allow deep linking to pages
      match = @page_re.exec(window.location.href)
      if match
        @page = parseInt(match[1])
      else
        @page = 1

    toggleNewPost: (event) =>
      event.preventDefault()
      if !@newPostForm
        @toggleDiscussion()
        @isWaitingOnNewPost = true;
        return
      if @showed
        @newPostForm.slideDown(300)
      else
        @newPostForm.show()
      @toggleDiscussionBtn.addClass('shown')
      @toggleDiscussionBtn.find('.button-text').html(gettext("Hide Discussion"))
      @$("section.discussion").slideDown()
      @showed = true

    hideNewPost: (event) ->
      event.preventDefault()
      @newPostForm.slideUp(300)

    hideDiscussion: =>
      @$("section.discussion").slideUp()
      @toggleDiscussionBtn.removeClass('shown')
      @toggleDiscussionBtn.find('.button-text').html(gettext("Show Discussion"))
      @showed = false

    toggleDiscussion: (event) =>
      if @showed
        @hideDiscussion()
      else
        @toggleDiscussionBtn.addClass('shown')
        @toggleDiscussionBtn.find('.button-text').html(gettext("Hide Discussion"))

        if @retrieved
          @$("section.discussion").slideDown()
          @showed = true
        else
          $elem = @toggleDiscussionBtn
          @loadPage(
            $elem,
            =>
              @hideDiscussion()
              DiscussionUtil.discussionAlert(
                gettext("Sorry"),
                gettext("We had some trouble loading the discussion. Please try again.")
              )
          )

    loadPage: ($elem, error) =>
      discussionId = @$el.data("discussion-id")
      url = DiscussionUtil.urlFor('retrieve_discussion', discussionId) + "?page=#{@page}"
      DiscussionUtil.safeAjax
        $elem: $elem
        $loading: $elem
        takeFocus: true
        url: url
        type: "GET"
        dataType: 'json'
        success: (response, textStatus, jqXHR) => @renderDiscussion($elem, response, textStatus, discussionId)
        error: error

    renderDiscussion: ($elem, response, textStatus, discussionId) =>
      $elem.focus()
      user = new DiscussionUser(response.user_info)
      window.user = user
      DiscussionUtil.setUser(user)
      Content.loadContentInfos(response.annotated_content_info)
      DiscussionUtil.loadRoles(response.roles)

      @course_settings = new DiscussionCourseSettings(response.course_settings)
      @discussion = new Discussion()
      @discussion.reset(response.discussion_data, {silent: false})

      $discussion = $(Mustache.render $("script#_inline_discussion").html(), {'threads':response.discussion_data, 'discussionId': discussionId})
      if @$('section.discussion').length
        @$('section.discussion').replaceWith($discussion)
      else
        @$el.append($discussion)

      @newPostForm = $('.new-post-article')
      @threadviews = @discussion.map (thread) ->
        new DiscussionThreadInlineView el: @$("article#thread_#{thread.id}"), model: thread
      _.each @threadviews, (dtv) -> dtv.render()
      DiscussionUtil.bulkUpdateContentInfo(window.$$annotated_content_info)
      @newPostView = new NewPostView(
        el: @newPostForm,
        collection: @discussion,
        course_settings: @course_settings
      )
      @newPostView.render()
      @discussion.on "add", @addThread

      @retrieved = true
      @showed = true
      @renderPagination(response.num_pages)

      if @isWaitingOnNewPost
        @newPostForm.show()

    addThread: (thread, collection, options) =>
      # TODO: When doing pagination, this will need to repaginate. Perhaps just reload page 1?
      article = $("<article class='discussion-thread' id='thread_#{thread.id}'></article>")
      @$('section.discussion > .threads').prepend(article)
      threadView = new DiscussionThreadInlineView el: article, model: thread
      threadView.render()
      @threadviews.unshift threadView

    renderPagination: (numPages) =>
      pageUrl = (number) ->
        "?discussion_page=#{number}"
      params = DiscussionUtil.getPaginationParams(@page, numPages, pageUrl)
      thing = Mustache.render @paginationTemplate(), params
      @$('section.pagination').html(thing)

    navigateToPage: (event) =>
      event.preventDefault()
      window.history.pushState({}, window.document.title, event.target.href)
      currPage = @page
      @page = $(event.target).data('page-number')
      @loadPage(
        $(event.target),
        =>
          @page = currPage
          DiscussionUtil.discussionAlert(
            gettext("Sorry"),
            gettext("We had some trouble loading the threads you requested. Please try again.")
          )
      )
