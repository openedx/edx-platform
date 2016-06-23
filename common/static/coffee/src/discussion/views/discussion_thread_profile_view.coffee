if Backbone?
  class @DiscussionThreadProfileView extends Backbone.View
    render: ->
      @convertMath()
      @abbreviateBody()
      params = $.extend(@model.toJSON(),{permalink: @model.urlFor('retrieve')})
      if not @model.get('anonymous')
        params = $.extend(params, user:{username: @model.username, user_url: @model.user_url})
      @$el.html(_.template($("#profile-thread-template").html())(params))
      @$("span.timeago").timeago()
      element = @$(".post-body")
      if MathJax?
        MathJax.Hub.Queue ["Typeset", MathJax.Hub, element[0]]
      @

    convertMath: ->
      @model.set('markdownBody', DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight @model.get('body'))

    abbreviateBody: ->
      abbreviated = DiscussionUtil.abbreviateHTML @model.get('markdownBody'), 140
      @model.set('abbreviatedBody', abbreviated)
