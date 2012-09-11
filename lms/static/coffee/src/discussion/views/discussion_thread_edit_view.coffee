class @DiscussionThreadEditView extends Backbone.View

  events:
    "click .post-update": "update"
    "click .post-cancel": "cancel_edit"

  template: _.template($("#thread-edit-template").html())

  $: (selector) ->
    @$el.find(selector)

  initialize: ->
    super()

  render: ->
    @$el.html(@template(@model.toJSON()))
    @delegateEvents()
    DiscussionUtil.makeWmdEditor @$el, $.proxy(@$, @), "edit-post-body"
    @$(".edit-post-tags").tagsInput DiscussionUtil.tagsInputOptions()
    @

  update: (event) ->
    @trigger "thread:update", event

  cancel_edit: (event) ->
    @trigger "thread:cancel_edit", event
