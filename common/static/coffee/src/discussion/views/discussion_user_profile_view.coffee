if Backbone?
  class @DiscussionUserProfileView extends Backbone.View
    events:
      "click .discussion-paginator a": "changePage"

    initialize: (options) ->
      super()
      @page = options.page
      @numPages = options.numPages
      @discussion = new Discussion()
      @discussion.on("reset", @render)
      @discussion.reset(@collection, {silent: false})

    render: () =>
      @$el.html(_.template($("#user-profile-template").html())({threads: @discussion.models}))
      @discussion.map (thread) ->
        new DiscussionThreadProfileView(el: @$("article#thread_#{thread.id}"), model: thread).render()
      baseUri = URI(window.location).removeSearch("page")
      pageUrlFunc = (page) -> baseUri.clone().addSearch("page", page)
      paginationParams = DiscussionUtil.getPaginationParams(@page, @numPages, pageUrlFunc)
      @$el.find(".discussion-pagination").html(_.template($("#pagination-template").html())(paginationParams))

    changePage: (event) ->
      event.preventDefault()
      url = $(event.target).attr("href")
      DiscussionUtil.safeAjax
        $elem: @$el
        $loading: $(event.target)
        takeFocus: true
        url: url
        type: "GET"
        dataType: "json"
        success: (response, textStatus, xhr) =>
          @page = response.page
          @numPages = response.num_pages
          @discussion.reset(response.discussion_data, {silent: false})
          history.pushState({}, "", url)
          $("html, body").animate({ scrollTop: 0 });
        error: =>
          DiscussionUtil.discussionAlert(
            gettext("Sorry"),
            gettext("We had some trouble loading the page you requested. Please try again.")
          )
