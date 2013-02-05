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
          span_el = e.currentTarget
          span_id = span_el.getAttribute('data-span-id')
          discussion_id = @getDiscussionId(span_id)
          discussion_el = @getDiscussionEl(discussion_id)
          span = {
            id: span_id
            el: span_el 
          }
          discussion = { 
            id: discussion_id
            el: discussion_el 
          }
          fn.call this, span, discussion

    onClickSpan: (span, discussion) ->
        @scrollToDiscussion(discussion.el)
        
    onEnterSpan: (span, discussion) ->
        @focusDiscussion(discussion.el, true)
    
    onLeaveSpan: (span, discussion) ->
        @focusDiscussion(discussion.el, false)
        
    focusDiscussion: (el, state) ->
        $(@discussionSelector, @el).not(el).toggleClass('opaque', state)

    scrollToDiscussion: (el) ->
        padding = 20
        complete = @makeHighlighter(el)
        animOpts = {
            scrollTop : el.offset().top - padding
        }
        
        if @canScrollToDiscussion(el)
            $('html, body').animate(animOpts, 500, 'swing', complete)
        else
            complete()

    canScrollToDiscussion: (el) ->
        scrollTop = el.offset().top
        docHeight = $(document).height()
        winHeight = $(window).height()
        winScrollTop = window.scrollY

        viewStart = winScrollTop
        viewEnd = winScrollTop + (.75 * winHeight)
        inView = viewStart < scrollTop < viewEnd

        scrollable = !inView
        atDocEnd = viewStart + winHeight >= docHeight

        return (if atDocEnd then false else scrollable)
    
    makeHighlighter: (el) ->
        return @_once -> el.effect('highlight', {}, 500)
            
    _once: (fn) ->
        done = false
        return => 
            fn.call this unless done
            done = true

    _bind: (fn) ->
        return => fn.apply(this, arguments)
