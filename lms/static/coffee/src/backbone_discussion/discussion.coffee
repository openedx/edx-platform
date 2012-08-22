class @Discussion extends Backbone.Collection
  model: Thread

  initialize: ->
    DiscussionUtil.addDiscussion @id, @
    @bind "add", (item) =>
      item.discussion = @

  find: (id) ->
    _.first @where(id: id)

class @DiscussionModuleView extends Backbone.View

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

  search: ->

  sort: ->

  page: ->

  events:
    "submit .search-wrapper>.discussion-search-form": "search"
    "click .discussion-search-link": "search"
    "click .discussion-sort-link": "sort"
    "click .discussion-paginator>.discussion-page-link": "page"
