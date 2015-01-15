if Backbone?
  class @ResponseCommentShowView extends DiscussionContentShowView
    tagName: "li"

    render: ->
      @template = _.template($("#response-comment-show-template").html())
      @$el.html(
        @template(
          _.extend(
            {
              cid: @model.cid,
              author_display: @getAuthorDisplay()
            },
            @model.attributes
          )
        )
      )

      @delegateEvents()
      @renderAttrs()
      @$el.find(".timeago").timeago()
      @convertMath()
      @addReplyLink()
      @

    addReplyLink: () ->
      if @model.hasOwnProperty('parent')
        name = @model.parent.get('username') ? gettext("anonymous")
        html = "<a href='#comment_#{@model.parent.id}'>@#{name}</a>:  "
        p = @$('.response-body p:first')
        p.prepend(html)

    convertMath: ->
      body = @$el.find(".response-body")
      body.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight body.text()
      if MathJax?
        MathJax.Hub.Queue ["Typeset", MathJax.Hub, body[0]]

    _delete: (event) =>
        @trigger "comment:_delete", event

    edit: (event) =>
      @trigger "comment:edit", event
