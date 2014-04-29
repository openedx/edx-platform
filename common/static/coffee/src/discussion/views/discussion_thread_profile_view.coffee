if Backbone?
  class @DiscussionThreadProfileView extends Backbone.View
    render: ->
      @template = DiscussionUtil.getTemplate("_profile_thread")
      if not @model.has('abbreviatedBody')
        @abbreviateBody()
      params = $.extend(@model.toJSON(),{permalink: @model.urlFor('retrieve')})
      if not @model.get('anonymous')
        params = $.extend(params, user:{username: @model.username, user_url: @model.user_url})
      @$el.html(Mustache.render(@template, params))
      @$("span.timeago").timeago()
      @convertMath()
      @

    convertMath: ->
      element = @$(".post-body")
      element.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight element.text()
      MathJax.Hub.Queue ["Typeset", MathJax.Hub, element[0]]

    abbreviateBody: ->
      abbreviated = DiscussionUtil.abbreviateString @model.get('body'), 140
      @model.set('abbreviatedBody', abbreviated)
