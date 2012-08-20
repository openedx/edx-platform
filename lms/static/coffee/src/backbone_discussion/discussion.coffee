$ ->
  
  class Discussion extends Backbone.Collection
    model: Thread
    initialize: ->
      this.bind "add", (item) =>
        item.collection = this

  class DiscussionModuleView extends Backbone.View

  class DiscussionView extends Backbone.View

    $: (selector) ->
      @$local.find(selector)

    initialize: ->
      @$local = @$el.children(".local")

    events:
      "submit .search-wrapper>.discussion-search-form": "search"
      "click .discussion-search-link": "search"
      "click .discussion-sort-link": "sort"
      "click .discussion-paginator>.discussion-page-link": "page"
  
  $(".discussion-module").each (index, elem) ->
    view = new DiscussionModuleView(el: elem)

  $("section.discussion").each (index, elem) ->
    discussionData = DiscussionUtil.getDiscussionData(elem)
    discussion = new Discussion(discussionData)
    view = new DiscussionView(el: elem, model: discussion)
