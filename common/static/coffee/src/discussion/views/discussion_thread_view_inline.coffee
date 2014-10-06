if Backbone?
  class @DiscussionThreadInlineView extends DiscussionThreadView
    expanded = false
    events:
      "click .discussion-submit-post": "submitComment"
      "click .expand-post": "expandPost"
      "click .collapse-post": "collapsePost"
      "click .add-response-btn": "scrollToAddResponse"

    initialize: ->
      super()

    initLocal: ->
      @$local = @$el.children(".discussion-article").children(".local")
      if not @$local.length
        @$local = @$el
      @$delegateElement = @$local

    renderTemplate: () ->
      if @model.has('group_id')
        @template = DiscussionUtil.getTemplate("_inline_thread_cohorted")
      else
        @template = DiscussionUtil.getTemplate("_inline_thread")

      if not @model.has('abbreviatedBody')
        @abbreviateBody()
      params = @model.toJSON()
      Mustache.render(@template, params)

    render: () ->
      super()
      @$el.find('.post-extended-content').hide()
      @$el.find('.collapse-post').hide()

    getShowViewClass: () ->
      return DiscussionThreadInlineShowView

    loadInitialResponses: () ->
      if @expanded
        super()

    abbreviateBody: ->
      abbreviated = DiscussionUtil.abbreviateString @model.get('body'), 140
      @model.set('abbreviatedBody', abbreviated)

    expandPost: (event) =>
      @$el.addClass('expanded')
      @$el.find('.post-body').text(@model.get('body'))
      @showView.convertMath()
      @$el.find('.expand-post').css('display', 'none')
      @$el.find('.collapse-post').css('display', 'block')
      @$el.find('.post-extended-content').show()
      if not @expanded
        @expanded = true
        @loadInitialResponses()

    collapsePost: (event) ->
      curScroll = $(window).scrollTop()
      postTop = @$el.offset().top
      if postTop < curScroll
        $('html, body').animate({scrollTop: postTop})
      @$el.removeClass('expanded')
      @$el.find('.post-body').text(@model.get('abbreviatedBody'))
      @showView.convertMath()
      @$el.find('.expand-post').css('display', 'block')
      @$el.find('.collapse-post').css('display', 'none')
      @$el.find('.post-extended-content').hide()

    createEditView: () ->
      super()
      @editView.bind "thread:update", @abbreviateBody
