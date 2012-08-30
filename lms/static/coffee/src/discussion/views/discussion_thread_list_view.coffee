class @DiscussionThreadListView extends Backbone.View
  template: _.template($("#thread-list-template").html())
  events:
    "click .search": "showSearch"
    "keyup .post-search-field": "performSearch"

  render: ->
    @timer = 0;
    @$el.html(@template())
    @collection.on "reset", @renderThreads
    @renderThreads()
    @

  renderThreads: =>
    @$(".post-list").html("")
    @collection.each @renderThreadListItem

  renderThreadListItem: (thread) =>
    view = new ThreadListItemView(model: thread)
    view.on "thread:selected", @threadSelected
    view.render()
    @$(".post-list").append(view.el)

  threadSelected: (thread_id) =>
    @setActiveThread(thread_id)
    @trigger("thread:selected", thread_id)

  setActiveThread: (thread_id) ->
    @$("a").removeClass("active")
    @$("a[data-id='#{thread_id}']").addClass("active")

  showSearch: ->
    @$(".search").addClass('is-open');
    @$(".browse").removeClass('is-open');
    setTimeout (-> @$(".post-search-field").focus()), 200

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
          console.log textStatus
          if textStatus == 'success'
            @collection.reset(response.discussion_data)
            console.log(@collection)

    @delay(callback, 300)
