if Backbone?
  class @ThreadResponseEditView extends Backbone.View

    events:
      "click .post-update": "update"
      "click .post-cancel": "cancel_edit"

    $: (selector) ->
      @$el.find(selector)

    initialize: ->
      super()

    render: ->
      @template = _.template($("#thread-response-edit-template").html())
      @$el.html(@template(@model.toJSON()))
      @delegateEvents()
      DiscussionUtil.makeWmdEditor @$el, $.proxy(@$, @), "edit-post-body"
      @

    update: (event) ->
      @trigger "response:update", event

    cancel_edit: (event) ->
      @trigger "response:cancel_edit", event
