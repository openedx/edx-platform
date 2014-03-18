if Backbone?
  class @ResponseCommentEditView extends Backbone.View

    events:
      "click .post-update": "update"
      "click .post-cancel": "cancel_edit"

    $: (selector) ->
      @$el.find(selector)

    initialize: ->
      super()

    render: ->
      @template = _.template($("#response-comment-edit-template").html())
      @$el.html(@template(@model.toJSON()))
      @delegateEvents()
      DiscussionUtil.makeWmdEditor @$el, $.proxy(@$, @), "edit-comment-body"
      @

    update: (event) ->
      @trigger "comment:update", event

    cancel_edit: (event) ->
      @trigger "comment:cancel_edit", event
