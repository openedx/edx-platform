if Backbone?
  class @ResponseCommentView extends DiscussionContentView
    tagName: "li"
    template: _.template($("#response-comment-template").html())
    initLocal: ->
      # TODO .response-local is the parent of the comments so @$local is null, not sure what was intended here...
      @$local = @$el.find(".response-local")
      @$delegateElement = @$local

    render: ->
      params = @model.toJSON()
      params['deep'] = @options.deep
      if @options.deep
        params['parent_id'] = @options.parent.id
        params['parent_username'] = @options.parent.get('username')
      @$el.html(@template(params))
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
