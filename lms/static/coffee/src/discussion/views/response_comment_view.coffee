if Backbone?
  class @ResponseCommentView extends DiscussionContentView
    tagName: "li"
    template: _.template($("#response-comment-template").html())
    initLocal: ->
      # TODO .response-local is the parent of the comments so @$local is null, not sure what was intended here...
      @$local = @$el.find(".response-local")
      @$delegateElement = @$local

    render: ->
      @$el.html(@template(@model.toJSON()))
      @initLocal()
      @delegateEvents()
      @renderAttrs()
      @$el.find(".timeago").timeago()
      @convertMath()
      @
    convertMath: ->
      body = @$el.find(".response-body")
      body.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight body.html()
      # This removes paragraphs so that comments are more compact
      body.children("p").each (index, elem) ->
        $(elem).replaceWith($(elem).html())
      MathJax.Hub.Queue ["Typeset", MathJax.Hub, body[0]]
