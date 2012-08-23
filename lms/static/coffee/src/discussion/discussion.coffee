if Backbone?
  class @Discussion extends Backbone.Collection
    model: Thread

    initialize: ->
      DiscussionUtil.addDiscussion @id, @
      @bind "add", (item) =>
        item.discussion = @

    find: (id) ->
      _.first @where(id: id)

    addThread: (thread, options) ->
      options ||= {}
      model = new Thread thread
      @add model
      model

  class @DiscussionView extends Backbone.View

    $: (selector) ->
      @$local.find(selector)

    initLocal: ->
      @$local = @$el.children(".local")
      @$delegateElement = @$local

    initialize: ->
      @initLocal()
      @model.id = @$el.attr("_id")
      @model.view = @
      @$el.children(".threads").children(".thread").each (index, elem) =>
        threadView = new ThreadView el: elem, model: @model.find $(elem).attr("_id")
      if @$el.hasClass("forum-discussion")
        $(".discussion-sidebar").find(".sidebar-new-post-button")
                                .unbind('click').click $.proxy @newPost, @
      else if @$el.hasClass("inline-discussion")
        @newPost()

    reload: ($elem, url) ->
      if not url then return
      DiscussionUtil.safeAjax
        $elem: $elem
        $loading: $elem
        url: url
        type: "GET"
        success: (response, textStatus) =>
          $parent = @$el.parent()
          @$el.replaceWith(response.html)
          $discussion = $parent.find("section.discussion")
          @model.reset(response.discussionData, { silent: false })
          view = new DiscussionView el: $discussion[0], model: @model
          DiscussionUtil.bulkUpdateContentInfo(window.$$annotated_content_info)
          $("html, body").animate({ scrollTop: 0 }, 0)

    loadSimilarPost: (event) ->
      $title = @$(".new-post-title")
      $wrapper = @$(".new-post-similar-posts-wrapper")
      $similarPosts = @$(".new-post-similar-posts")
      prevText = $title.attr("prev-text")
      text = $title.val()
      if text == prevText
        if @$(".similar-post").length
          $wrapper.show()
      else if $.trim(text).length
        $elem = $(event.target)
        url = DiscussionUtil.urlFor 'search_similar_threads', @model.id
        data = { text: @$(".new-post-title").val() }
        DiscussionUtil.get $elem, url, data, (response, textStatus) =>
          $similarPosts.empty()
          if $.type(response) == "array" and response.length
            $wrapper.show()
            for thread in response
              $similarPost = $("<a>").addClass("similar-post")
                                     .html(thread["title"])
                                     .attr("href", "javascript:void(0)") #TODO
                                     .appendTo($similarPosts)
          else
            $wrapper.hide()
      else
        $wrapper.hide()
      $title.attr("prev-text", text)


    newPost: ->
      if not @$(".wmd-panel").length
        view = { discussion_id: @model.id }
        @$el.children(".discussion-non-content").append Mustache.render DiscussionUtil.getTemplate("_new_post"), view
        $newPostBody = @$(".new-post-body")
        DiscussionUtil.makeWmdEditor @$el, $.proxy(@$, @), "new-post-body"

        $input = DiscussionUtil.getWmdInput @$el, $.proxy(@$, @), "new-post-body"
        $input.attr("placeholder", "post a new topic...")
        if @$el.hasClass("inline-discussion")
          $input.bind 'focus', (e) =>
            @$(".new-post-form").removeClass('collapsed')
        else if @$el.hasClass("forum-discussion")
          @$(".new-post-form").removeClass('collapsed')

        @$(".new-post-tags").tagsInput DiscussionUtil.tagsInputOptions()

        @$(".new-post-title").blur $.proxy(@loadSimilarPost, @)

        @$(".hide-similar-posts").click =>
          @$(".new-post-similar-posts-wrapper").hide()

        @$(".discussion-submit-post").click $.proxy(@submitNewPost, @)
        @$(".discussion-cancel-post").click $.proxy(@cancelNewPost, @)
        

      @$(".new-post-form").show()

    submitNewPost: (event) ->
      title = @$(".new-post-title").val()
      body = DiscussionUtil.getWmdContent @$el, $.proxy(@$, @), "new-post-body"
      tags = @$(".new-post-tags").val()
      anonymous = false || @$(".discussion-post-anonymously").is(":checked")
      autowatch = false || @$(".discussion-auto-watch").is(":checked")
      url = DiscussionUtil.urlFor('create_thread', @model.id)
      DiscussionUtil.safeAjax
        $elem: $(event.target)
        $loading: $(event.target) if event
        url: url
        type: "POST"
        dataType: 'json'
        data:
          title: title
          body: body
          tags: tags
          anonymous: anonymous
          auto_subscribe: autowatch
        error: DiscussionUtil.formErrorHandler(@$(".new-post-form-errors"))
        success: (response, textStatus) =>
          DiscussionUtil.clearFormErrors(@$(".new-post-form-errors"))
          $thread = $(response.html)
          @$el.children(".threads").prepend($thread)

          @$(".new-post-title").val("")
          DiscussionUtil.setWmdContent @$el, $.proxy(@$, @), "new-post-body", ""
          @$(".new-post-tags").val("")
          @$(".new-post-tags").importTags("")

          thread = @model.addThread response.content
          threadView = new ThreadView el: $thread[0], model: thread
          thread.updateInfo response.annotated_content_info
          @cancelNewPost()
          

    cancelNewPost: (event) ->
      if @$el.hasClass("inline-discussion")
        @$(".new-post-form").addClass("collapsed")
      else if @$el.hasClass("forum-discussion")
        @$(".new-post-form").hide()

    search: (event) ->
      event.preventDefault()
      $elem = $(event.target)
      url = URI($elem.attr("action")).addSearch({text: @$(".search-input").val()})
      @reload($elem, url)

    sort: ->
      $elem = $(event.target)
      url = $elem.attr("sort-url")
      @reload($elem, url)

    page: (event) ->
      $elem = $(event.target)
      url = $elem.attr("page-url")
      @reload($elem, url)

    events:
      "submit .search-wrapper>.discussion-search-form": "search"
      "click .discussion-search-link": "search"
      "click .discussion-sort-link": "sort"
      "click .discussion-page-link": "page"
