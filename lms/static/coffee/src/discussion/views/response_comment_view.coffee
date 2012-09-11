if Backbone?
  class @ResponseCommentView extends DiscussionContentView
    tagName: "li"

    initLocal: ->
      # TODO .response-local is the parent of the comments so @$local is null, not sure what was intended here...
      @$local = @$el.find(".response-local")
      @$delegateElement = @$local

    render: ->
      @template = _.template($("#response-comment-template").html())
      params = @model.toJSON()
      params['deep'] = @model.has('parent')
      if @model.has('parent')
        params['parent_id'] = @model.get('parent').id
        params['parent_username'] = @model.get('parent').get('username')
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
