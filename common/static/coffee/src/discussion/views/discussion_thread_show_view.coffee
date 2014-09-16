if Backbone?
  class @DiscussionThreadShowView extends DiscussionContentShowView
    initialize: (options) ->
      super()
      @mode = options.mode or "inline"  # allowed values are "tab" or "inline"
      if @mode not in ["tab", "inline"]
        throw new Error("invalid mode: " + @mode)

    renderTemplate: ->
      @template = _.template($("#thread-show-template").html())
      context = $.extend(
        {
          mode: @mode,
          flagged: @model.isFlagged(),
          author_display: @getAuthorDisplay(),
          cid: @model.cid
        },
        @model.attributes,
      )
      @template(context)

    render: ->
      @$el.html(@renderTemplate())
      @delegateEvents()
      @renderAttrs()
      @$("span.timeago").timeago()
      @convertMath()
      @highlight @$(".post-body")
      @highlight @$("h1,h3")
      @

    convertMath: ->
      element = @$(".post-body")
      element.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight element.text()
      MathJax.Hub.Queue ["Typeset", MathJax.Hub, element[0]]

    edit: (event) ->
      @trigger "thread:edit", event

    _delete: (event) ->
      @trigger "thread:_delete", event

    highlight: (el) ->
      if el.html()
        el.html(el.html().replace(/&lt;mark&gt;/g, "<mark>").replace(/&lt;\/mark&gt;/g, "</mark>"))
