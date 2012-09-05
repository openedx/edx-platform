class @ResponseCommentView extends DiscussionContentView
  tagName: "li"
  template: _.template($("#response-comment-template").html())
  initLocal: ->
    @$local = @$el.find(".response-local")
    @$delegateElement = @$local

  render: ->
    @$el.html(@template(@model.toJSON()))
    @initLocal()
    @delegateEvents()
    @renderAttrs()
    @$(".timeago").timeago()
    @convertMath()
    @
  convertMath: ->
    body = @$(".response-body")
    body.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight body.html()
    body.children("p").each (index, elem) ->
      $(elem).replaceWith($(elem).html())
    MathJax.Hub.Queue ["Typeset", MathJax.Hub, body[0]]
