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
    if @$el.hasClass("forum-discussion")
      $(".discussion-sidebar").find(".sidebar-new-post-button")
                              .unbind('click').click $.proxy @newPost, @
    else if @$el.hasClass("inline-discussion")
      @newPost()

  reload: ($elem, url) ->
    if not url then return
    DiscussionUtil.get $elem, url, (response, textStatus) =>
      $discussion = $(response.html)
      $parent = @$el.parent()
      @$el.replaceWith($discussion)
      @model.reset(response.discussionData, { silent: false })
      view = new DiscussionView el: $discussion[0], model: @model
      DiscussionUtil.bulkUpdateContentInfo(window.$$annotated_content_info)

  newPost: ->

  search: (event) ->
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
