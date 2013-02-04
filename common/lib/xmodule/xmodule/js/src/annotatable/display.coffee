class @Annotatable
    @_debug: true

    wrapperSelector: '.annotatable-wrapper'
    spanSelector: 'span.annotatable[data-span-id]'
    discussionSelector: '.annotatable-discussion[data-discussion-id]'
 
    constructor: (el) ->
        console.log 'loaded Annotatable' if @_debug
        @el = el
        @init()

    init: () ->
        @loadSpanData()
        @initEvents()

    initEvents: () ->
        $(@wrapperSelector, @el).delegate(@spanSelector, {
            'click': @_bind @onSpanEvent @onClickSpan
            'mouseenter': @_bind @onSpanEvent @onEnterSpan
            'mouseleave': @_bind @onSpanEvent @onLeaveSpan
        })

    loadSpanData: () ->
        @spandata = $(@wrapperSelector, @el).data('spans')
        
    getDiscussionId: (span_id) ->
        @spandata[span_id]
        
    getDiscussionEl: (discussion_id) ->
        $(@discussionSelector, @el).filter('[data-discussion-id="'+discussion_id+'"]')

    onSpanEvent: (fn) ->
        (e) =>
          span_id = e.target.getAttribute('data-span-id')
          discussion_id = @getDiscussionId(span_id)
          span = {
            id: span_id, 
            el: e.target 
          }
          discussion = { 
              id: discussion_id, 
              el: @getDiscussionEl(discussion_id)
          }
          fn.call this, span, discussion

    onClickSpan: (span, discussion) ->
        @scrollToDiscussion(discussion.el)
        
    onEnterSpan: (span, discussion) ->
        $(@discussionSelector, @el).not(discussion.el).toggleClass('opaque', true)
    
    onLeaveSpan: (span, discussion) ->
        $(@discussionSelector, @el).not(discussion.el).toggleClass('opaque', false)

    scrollToDiscussion: (el) ->
        complete = @makeHighlighter(el)
        top = el.offset().top - 20 # with some padding

        $('html, body').animate({ scrollTop: top }, 750, 'swing', complete)
    
    makeHighlighter: (el) ->
        return @_once -> el.effect('highlight', {}, 750)
            
    _once: (fn) ->
        done = false
        return => 
            fn.call this unless done
            done = true

    _bind: (fn) ->
        return => fn.apply(this, arguments)
