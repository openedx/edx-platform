class @Annotatable
    @_debug: true

    wrapperSelector: '.annotatable-wrapper'
    toggleSelector:  '.annotatable-toggle'
    spanSelector:    '.annotatable-span'
    replySelector:   '.annotatable-reply'
    helpSelector:    '.annotatable-help-icon'
    returnSelector:  '.annotatable-return'

    discussionXModuleSelector: '.xmodule_DiscussionModule'
    discussionSelector:        '.discussion-module'

    constructor: (el) ->
        console.log 'loaded Annotatable' if @_debug
        @el = el
        @init()

    $: (selector) ->
        $(selector, @el)

    init: () ->
        @initEvents()
        @initTips()
        @initDiscussion()

    initEvents: () ->
        @annotationsHidden = false
        @$(@toggleSelector).bind 'click', @onClickToggleAnnotations
        @$(@wrapperSelector).delegate @replySelector, 'click', @onClickReply
        $(@discussionXModuleSelector).delegate @returnSelector, 'click', @onClickReturn

    initDiscussion: () ->
        1
  
    initTips: () ->
        @savedTips = []
        @$(@spanSelector).each (index, el) => $(el).qtip(@getTipOptions el)
        @$(@helpSelector).qtip
            position:
                my: 'right top'
                at: 'bottom left'
                container: @$(@wrapperSelector)
            content:
                title: 'Annotated Reading'
                text: true # use title attribute of this element

    getTipOptions: (el) ->
        content:
            title:
                text: @makeTipTitle(el)
            text: @makeTipContent(el)
        position:
            my: 'bottom center' # of tooltip
            at: 'top center' # of target
            target: 'mouse'
            container: @$(@wrapperSelector)
            adjust:
                mouse: false # dont follow the mouse
                y: -10
        show:
            event: 'mouseenter'
            solo: true
        hide:
            event: 'unfocus'
        style:
            classes: 'ui-tooltip-annotatable'
        events:
            show: @onShowTip

    onShowTip: (event, api) =>
        event.preventDefault() if @annotationsHidden

    onClickToggleAnnotations: (e) =>
        @toggleAnnotations()

    onClickReply: (e) =>
        e.preventDefault()

        problem_el = @getProblemEl e.currentTarget
        if problem_el.length == 1
            @scrollTo(problem_el, @afterScrollToProblem)
        else
            console.log 'Problem not found! Event: ', e

    onClickReturn: (e) =>
        e.preventDefault()

        el = @getSpan e.currentTarget
        offset = -200

        @scrollTo(el, @afterScrollToSpan, offset)

    getSpan: (el) ->
        span_id = @getSpanId(el)
        @$(@spanSelector).filter("[data-span-id='#{span_id}']")
    
    getDiscussion: (el) ->
        discussion_id = @getDiscussionId()
        $(@discussionXModuleSelector).find(@discussionSelector).filter("[data-discussion-id='#{discussion_id}']")

    getProblem: (el) ->
        el # TODO

    getProblemId: (el) ->
        $(el).data('problem-id')

    getSpanId: (el) ->
        $(el).data('span-id')
        
    getDiscussionId: () ->
        @$(@wrapperSelector).data('discussion-id')

    toggleAnnotations: () ->
        hide = (@annotationsHidden = not @annotationsHidden)
        @toggleButtonText hide
        @toggleSpans hide
        @toggleReturnLinks hide
        @toggleTips hide

    toggleTips: (hide) ->
        if hide then @closeAndSaveTips() else @openSavedTips()

    toggleReturnLinks: (hide) ->
        $(@returnSelector)[if hide then 'hide' else 'show']()

    toggleButtonText: (hide) ->
        buttonText = (if hide then 'Show' else 'Hide')+' Annotations'
        @$(@toggleSelector).text(buttonText)

    toggleSpans: (hide) ->
        @$(@spanSelector).toggleClass 'hide', hide, 250

    scrollTo: (el, after, offset = -20) ->
        $('html,body').scrollTo(el, {
            duration: 500
            onAfter: @_once => after?.call this, el
            offset: offset
        }) if el
 
    afterScrollToDiscussion: (discussion_el) ->
        btn = $('.discussion-show', discussion_el)
        btn.click() if !btn.hasClass('shown')

    afterScrollToProblem: (problem_el) ->
        problem_el.effect 'highlight', {}, 500

    afterScrollToSpan: (span_el) ->
        span_el.effect 'highlight', {color: 'rgba(0,0,0,0.5)' }, 1000

    makeTipContent: (el) ->
        (api) =>
            text = $(el).data('comment-body')
            comment = @createCommentEl(text)
            reply = @createReplyLink('dummy-problem-id')
            $(comment).add(reply)

    makeTipTitle: (el) ->
        (api) =>
            title = $(el).data('comment-title')
            (if title then title else 'Commentary')

    createCommentEl: (text) ->
        $("<div class=\"annotatable-comment\">#{text}</div>")

    createReplyLink: (problem_id) ->
        $("<a class=\"annotatable-reply\" href=\"javascript:void(0);\" data-problem-id=\"#{problem_id}\">Reply to Annotation</a>")

    createReturnLink: (span_id) ->
        $("<a class=\"annotatable-return\" href=\"javascript:void(0);\" data-span-id=\"#{span_id}\">Return to annotation</a>")

    openSavedTips: () ->
        @showTips @savedTips

    closeAndSaveTips: () ->
        @savedTips = @findVisibleTips()
        @hideTips @savedTips

    findVisibleTips: () ->
        visible = []
        @$(@spanSelector).each (index, el) ->
            api = $(el).qtip('api')
            tip = $(api?.elements.tooltip)
            if tip.is(':visible')
                visible.push [el, tip.offset()]
        visible

    hideTips: (pairs) ->
        elements = (pair[0] for pair in pairs)
        $(elements).qtip('hide')

    showTips: (pairs) ->
        $.each pairs, (index, pair) ->
            [el, offset] = pair
            $(el).qtip('show')
            api = $(el).qtip('api')
            $(api?.elements.tooltip).offset(offset)
 
    _once: (fn) ->
        done = false
        return =>
            fn.call this unless done
            done = true