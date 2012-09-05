if Backbone?
  class @Discussion extends Backbone.Collection
    model: Thread

    initialize: ->
      @bind "add", (item) =>
        item.discussion = @
      @comparator = @sortByDateRecentFirst
      @on "thread:remove", (thread) =>
        console.log "remove triggered"
        @remove(thread)

    find: (id) ->
      _.first @where(id: id)

    addThread: (thread, options) ->
      options ||= {}
      model = new Thread thread
      @add model
      model

    sortByDate: (thread) ->
      thread.get("created_at")

    sortByDateRecentFirst: (thread) ->
      -(new Date(thread.get("created_at")).getTime())
      #return String.fromCharCode.apply(String, 
      #  _.map(thread.get("created_at").split(""), 
      #        ((c) -> return 0xffff - c.charChodeAt()))
      #)

    sortByVotes: (thread1, thread2) ->
      thread1_count = parseInt(thread1.get("votes")['up_count'])
      thread2_count = parseInt(thread2.get("votes")['up_count'])
      thread2_count - thread1_count

    sortByComments: (thread1, thread2) ->
      thread1_count = parseInt(thread1.get("comments_count"))
      thread2_count = parseInt(thread2.get("comments_count"))
      thread2_count - thread1_count

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
        loadingCallback: ->
          $(this).parent().append("<span class='discussion-loading'></span>")
        loadedCallback: ->
          $(this).parent().children(".discussion-loading").remove()
        url: url
        type: "GET"
        success: (response, textStatus) =>
          $parent = @$el.parent()
          @$el.replaceWith(response.html)
          $discussion = $parent.find("section.discussion")
          @model.reset(response.discussion_data, { silent: false })
          view = new DiscussionView el: $discussion[0], model: @model
          DiscussionUtil.bulkUpdateContentInfo(window.$$annotated_content_info)
          $("html, body").animate({ scrollTop: 0 }, 0)

    loadSimilarPost: (event) ->
      console.log "loading similar"
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
        DiscussionUtil.safeAjax
          $elem: $elem
          url: url
          data: data
          dataType: 'json'
          success: (response, textStatus) =>
            $wrapper.html(response.html)
            if $wrapper.find(".similar-post").length
              $wrapper.show()
              $wrapper.find(".hide-similar-posts").click =>
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
        

      @$el.children(".blank").hide()
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

          @$el.children(".blank").remove()

          @$(".new-post-similar-posts").empty()
          @$(".new-post-similar-posts-wrapper").hide()
          @$(".new-post-title").val("").attr("prev-text", "")
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
      @$el.children(".blank").show()

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
