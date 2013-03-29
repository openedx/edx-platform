if Backbone?
  class @DiscussionModuleView extends Backbone.View
    events:
      "click .discussion-show": "toggleDiscussion"
      "click .new-post-btn": "toggleNewPost"
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

    toggleNewPost: (event) ->
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
      @toggleDiscussionBtn.find('.button-text').html("Hide Discussion")
      @$("section.discussion").slideDown()
      @showed = true

    hideNewPost: (event) ->
      event.preventDefault()
      @newPostForm.slideUp(300)

    toggleDiscussion: (event) ->
      if @showed
        @$("section.discussion").slideUp()
        @toggleDiscussionBtn.removeClass('shown')
        @toggleDiscussionBtn.find('.button-text').html("Show Discussion")
        @showed = false
      else
        @toggleDiscussionBtn.addClass('shown')
        @toggleDiscussionBtn.find('.button-text').html("Hide Discussion")

        if @retrieved
          @$("section.discussion").slideDown()
          @showed = true
        else
          $elem = @toggleDiscussionBtn
          @loadPage $elem

    loadPage: ($elem)=>
      discussionId = @$el.data("discussion-id")
      url = DiscussionUtil.urlFor('retrieve_discussion', discussionId) + "?page=#{@page}"
      DiscussionUtil.safeAjax
        $elem: $elem
        $loading: $elem
        url: url
        type: "GET"
        dataType: 'json'
        success: (response, textStatus, jqXHR) => @renderDiscussion($elem, response, textStatus, discussionId)

    renderDiscussion: ($elem, response, textStatus, discussionId) =>
      window.user = new DiscussionUser(response.user_info)
      Content.loadContentInfos(response.annotated_content_info)
      DiscussionUtil.loadRoles(response.roles)
      allow_anonymous = response.allow_anonymous
      allow_anonymous_to_peers = response.allow_anonymous_to_peers
      cohorts = response.cohorts
      # $elem.html("Hide Discussion")
      @discussion = new Discussion()
      @discussion.reset(response.discussion_data, {silent: false})

      #use same discussion template but different thread templated
      #determined in the coffeescript based on whether or not there's a
      #group id
      
      if response.is_cohorted and response.is_moderator
        source = "script#_inline_discussion_cohorted"
      else
        source = "script#_inline_discussion"
      
      $discussion = $(Mustache.render $(source).html(), {'threads':response.discussion_data, 'discussionId': discussionId, 'allow_anonymous_to_peers': allow_anonymous_to_peers, 'allow_anonymous': allow_anonymous, 'cohorts':cohorts})
      if @$('section.discussion').length
        @$('section.discussion').replaceWith($discussion)
      else
        @$el.append($discussion)
      @newPostForm = $('.new-post-article')
      @threadviews = @discussion.map (thread) ->
        new DiscussionThreadInlineView el: @$("article#thread_#{thread.id}"), model: thread
      _.each @threadviews, (dtv) -> dtv.render()
      DiscussionUtil.bulkUpdateContentInfo(window.$$annotated_content_info)
      @newPostView = new NewPostInlineView el: @$('.new-post-article'), collection: @discussion
      @discussion.on "add", @addThread
      @retrieved = true
      @showed = true
      @renderPagination(2, response.num_pages)
      if @isWaitingOnNewPost
        @newPostForm.show()

    addThread: (thread, collection, options) =>
      # TODO: When doing pagination, this will need to repaginate. Perhaps just reload page 1?
      article = $("<article class='discussion-thread' id='thread_#{thread.id}'></article>")
      @$('section.discussion > .threads').prepend(article)
      threadView = new DiscussionThreadInlineView el: article, model: thread
      threadView.render()
      @threadviews.unshift threadView

    renderPagination: (delta, numPages) =>
      minPage = Math.max(@page - delta, 1)
      maxPage = Math.min(@page + delta, numPages)
      pageUrl = (number) ->
        "?discussion_page=#{number}"
      params =
        page: @page
        lowPages: _.range(minPage, @page).map (n) -> {number: n, url: pageUrl(n)}
        highPages: _.range(@page+1, maxPage+1).map (n) -> {number: n, url: pageUrl(n)}
        previous: if @page-1 >= 1 then {url: pageUrl(@page-1), number: @page-1} else false
        next: if @page+1 <= numPages then {url: pageUrl(@page+1), number: @page+1} else false
        leftdots: minPage > 2
        rightdots: maxPage < numPages-1
        first: if minPage > 1 then {url: pageUrl(1)} else false
        last: if maxPage < numPages then {number: numPages, url: pageUrl(numPages)} else false
      thing = Mustache.render @paginationTemplate(), params
      @$('section.pagination').html(thing)

    navigateToPage: (event) =>
      event.preventDefault()
      window.history.pushState({}, window.document.title, event.target.href)
      @page = $(event.target).data('page-number')
      @loadPage($(event.target))
