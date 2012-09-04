class @ResponseCommentView extends DiscussionContentView
  tagName: "li"
  template: _.template($("#response-comment-template").html())
  render: ->
    @$el.html(@template(@model.toJSON()))
    @$(".timeago").timeago()
    @convertMath()
    @
  convertMath: ->
    body = @$(".response-body")
    body.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight body.html()
    body.children("p").each (index, elem) ->
      $(elem).replaceWith($(elem).html())
    MathJax.Hub.Queue ["Typeset", MathJax.Hub, body[0]]
