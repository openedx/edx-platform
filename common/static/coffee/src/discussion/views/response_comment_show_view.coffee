if Backbone?
  class @ResponseCommentShowView extends DiscussionContentView

    events:
      "click .discussion-flag-abuse": "toggleFlagAbuse"

    tagName: "li"

    initialize: ->
        super()
        @model.on "change", @updateModelDetails

    render: ->
      @template = _.template($("#response-comment-show-template").html())
      params = @model.toJSON()

      @$el.html(@template(params))
      @initLocal()
      @delegateEvents()
      @renderAttrs()
      @renderFlagged()
      @markAsStaff()
      @$el.find(".timeago").timeago()
      @convertMath()
      @addReplyLink()
      @

    addReplyLink: () ->
      if @model.hasOwnProperty('parent')
        name = @model.parent.get('username') ? "anonymous"
        html = "<a href='#comment_#{@model.parent.id}'>@#{name}</a>:  "
        p = @$('.response-body p:first')
        p.prepend(html)

    convertMath: ->
      body = @$el.find(".response-body")
      body.html DiscussionUtil.postMathJaxProcessor DiscussionUtil.markdownWithHighlight body.text()
      MathJax.Hub.Queue ["Typeset", MathJax.Hub, body[0]]

    markAsStaff: ->
      if DiscussionUtil.isStaff(@model.get("user_id"))
        @$el.find("a.profile-link").after('<span class="staff-label">staff</span>')
      else if DiscussionUtil.isTA(@model.get("user_id"))
        @$el.find("a.profile-link").after('<span class="community-ta-label">Community&nbsp;&nbsp;TA</span>')


    renderFlagged: =>
      if window.user.id in @model.get("abuse_flaggers") or (DiscussionUtil.isFlagModerator and @model.get("abuse_flaggers").length > 0)
        @$("[data-role=thread-flag]").addClass("flagged")
        @$("[data-role=thread-flag]").removeClass("notflagged")
      else
        @$("[data-role=thread-flag]").removeClass("flagged")
        @$("[data-role=thread-flag]").addClass("notflagged")

    updateModelDetails: =>
      @renderFlagged()


