class @Annotatable
    @_debug: true

    wrapperSelector: '.annotatable-wrapper'
    toggleSelector:  '.annotatable-toggle'
    spanSelector:    '.annotatable-span'
    commentSelector: '.annotatable-comment'
    replySelector:   '.annotatable-reply'
    returnSelector:  '.annotatable-return'
    helpSelector:    '.annotatable-help-icon'
    discussionXModuleSelector: '.xmodule_DiscussionModule'
    discussionSelector: '.discussion-module'
 
    constructor: (el) ->
        console.log 'loaded Annotatable' if @_debug
        @el = el
        @init()

    $: (selector) ->
        $(selector, @el)

    init: () ->
        @initEvents()
        @initTips()
        @initDiscussionReturnLinks()

    initEvents: () ->
        @annotationsHidden = false
        @$(@toggleSelector).bind 'click', @onClickToggleAnnotations
        @$(@wrapperSelector).delegate @replySelector, 'click', @onClickReply
        $(@discussionXModuleSelector).delegate @returnSelector, 'click', @onClickReturn

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

    initDiscussionReturnLinks: () ->
        $(@discussionXModuleSelector).find(@discussionSelector).each (index, el) =>
            $(el).after @createReturnLink(@getDiscussionId el)

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
        discussion_el = @getInlineDiscussion e.currentTarget
        @scrollTo(discussion_el, @afterScrollToDiscussion)

    onClickReturn: (e) =>
        e.preventDefault()
        @scrollTo(@getSpan e.currentTarget, @afterScrollToSpan)

    getSpan: (el) ->
        discussion_id = @getDiscussionId(el)
        @$(@spanSelector).filter("[data-discussion-id='#{discussion_id}']")
    
    getInlineDiscussion: (el) ->
        discussion_id = @getDiscussionId(el)
        $(@discussionXModuleSelector).find(@discussionSelector).filter("[data-discussion-id='#{discussion_id}']")

    getDiscussionId: (el) ->
        $(el).data('discussion-id')

    toggleAnnotations: () ->
        @annotationsHidden = not @annotationsHidden
        @toggleButtonText @annotationsHidden
        @toggleSpans @annotationsHidden
        @toggleTips @annotationsHidden

    toggleTips: (hide) ->
        if hide then @closeAndSaveTips() else @openSavedTips()

    toggleButtonText: (hide) ->
        buttonText = (if hide then 'Show' else 'Hide')+' Annotations'
        @$(@toggleSelector).text(buttonText)

    toggleSpans: (hide) ->
        @$(@spanSelector).toggleClass 'hide', hide

    scrollTo: (el, after) ->
        $('html,body').scrollTo(el, {
            duration: 500
            #onAfter: @_once => after.call this, el
        })
 
    afterScrollToDiscussion: () ->
        (el) ->
            btn = $('.discussion-show', el)
            btn.click() if !btn.hasClass('shown')

    afterScrollToSpan: (el) ->
        (el) -> el.effect('highlight', {}, 500)

    makeTipContent: (el) ->
        (api) =>
            discussion_id = @getDiscussionId(el)
            comment = $(@commentSelector, el).first().clone()
            comment = comment.after(@createReplyLink discussion_id) if discussion_id
            comment

    makeTipTitle: (el) ->
        (api) =>
            comment = $(@commentSelector, el).first()
            title = comment.attr('title')
            (if title then title else 'Commentary')

    createReplyLink: (discussion_id) ->
        $("<a class=\"annotatable-reply\" href=\"javascript:void(0);\" data-discussion-id=\"#{discussion_id}\">See Full Discussion</a>")

    createReturnLink: (discussion_id) ->
        $("<a class=\"annotatable-return button\" href=\"javascript:void(0);\" data-discussion-id=\"#{discussion_id}\">Return to annotation</a>")

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
