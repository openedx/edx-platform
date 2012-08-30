class @DiscussionThreadListView extends Backbone.View
  template: _.template($("#thread-list-template").html())
  events:
    "click .search": "showSearch"
    "click .browse": "toggleTopicDrop"
    "keyup .post-search-field": "performSearch"
    "click .sort-bar a": "sortThreads"

  render: ->
    @timer = 0;
    @$el.html(@template())
    @collection.on "reset", @renderThreads
    @renderThreads()
    @

  renderThreads: =>
    @$(".post-list").html("")
    @collection.each @renderThreadListItem
    @trigger "threads:rendered"

  renderThreadListItem: (thread) =>
    view = new ThreadListItemView(model: thread)
    view.on "thread:selected", @threadSelected
    view.render()
    @$(".post-list").append(view.el)

  threadSelected: (thread_id) =>
    @setActiveThread(thread_id)
    @trigger("thread:selected", thread_id)

  setActiveThread: (thread_id) ->
    @$(".post-list a").removeClass("active")
    @$("a[data-id='#{thread_id}']").addClass("active")

  showSearch: ->
    @$(".search").addClass('is-open')
    @$(".browse").removeClass('is-open')
    setTimeout (-> @$(".post-search-field").focus()), 200

  toggleTopicDrop: ->
    @$(".browse").toggleClass('is-dropped')
    if @$(".browse").hasClass('is-dropped')
      @$(".board-drop-menu").show()
    else
      @$(".board-drop-menu").hide()


  sortThreads: (event) ->
    @$(".sort-bar a").removeClass("active")
    $(event.target).addClass("active")
    sortBy = $(event.target).data("sort")
    if sortBy == "date"
      @collection.comparator = @collection.sortByDate
    else if sortBy == "votes"
      @collection.comparator = @collection.sortByVotes
    else if sortBy == "comments"
      @collection.comparator = @collection.sortByComments
    @collection.sort()



  delay: (callback, ms) =>
    clearTimeout(@timer)
    @timer = setTimeout(callback, ms)

  performSearch: ->
    callback = =>
      url = DiscussionUtil.urlFor("search")
      text = @$(".post-search-field").val()
      DiscussionUtil.safeAjax
        $elem: @$(".post-search-field")
        data: { text: text }
        url: url
        type: "GET"
        success: (response, textStatus) =>
          if textStatus == 'success'
            @collection.reset(response.discussion_data)

    @delay(callback, 300)
