if Backbone?
  class @ThreadResponseShowView extends DiscussionContentShowView
    initialize: ->
        super()
        @listenTo(@model, "change", @render)

    renderTemplate: ->
        @template = _.template($("#thread-response-show-template").html())
        context = _.extend(
            {
                cid: @model.cid,
                author_display: @getAuthorDisplay(),
                endorser_display: @getEndorserDisplay()
            },
            @model.attributes
        )
        @template(context)

    render: ->
      @$el.html(@renderTemplate())
      @delegateEvents()
      @renderAttrs()
      @$el.find(".posted-details .timeago").timeago()
      @convertMath()
      @

    convertMath: ->
      element = @$(".response-body")
      element.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight element.text()
      if MathJax?
        MathJax.Hub.Queue ["Typeset", MathJax.Hub, element[0]]

    edit: (event) ->
        @trigger "response:edit", event

    _delete: (event) ->
        @trigger "response:_delete", event
