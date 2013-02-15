class @Annotatable
    @_debug: true

    wrapperSelector: '.annotatable-wrapper'
    toggleSelector:  '.annotatable-toggle'
    spanSelector:    '.annotatable-span'
    commentSelector: '.annotatable-comment'
    replySelector:   '.annotatable-reply'
    helpSelector:    '.annotatable-help-icon'
    returnSelector:  '.annotatable-return'

    discussionXModuleSelector: '.xmodule_DiscussionModule'
    discussionSelector:        '.discussion-module'

    commentMaxLength: 750 # Max length characters to show in the comment hover state

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
            $(el).before @createReturnLink(@getDiscussionId el)

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
        return_el = discussion_el.prev(@returnSelector)

        if return_el.length == 1
            @scrollTo(return_el, () -> @afterScrollToDiscussion(discussion_el))
        else
            @scrollTo(discussion_el, @afterScrollToDiscussion)

    onClickReturn: (e) =>
        e.preventDefault()

        el = @getSpan e.currentTarget
        offset = -200

        @scrollTo(el, @afterScrollToSpan, offset)

    getSpan: (el) ->
        discussion_id = @getDiscussionId(el)
        @$(@spanSelector).filter("[data-discussion-id='#{discussion_id}']")
    
    getInlineDiscussion: (el) ->
        discussion_id = @getDiscussionId(el)
        $(@discussionXModuleSelector).find(@discussionSelector).filter("[data-discussion-id='#{discussion_id}']")

    getDiscussionId: (el) ->
        $(el).data('discussion-id')

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
        console.log(btn)
        btn.click() if !btn.hasClass('shown')

    afterScrollToSpan: (span_el) ->
        span_el.effect 'highlight', {color: 'rgba(0,0,0,0.5)' }, 1000

    makeTipContent: (el) ->
        (api) =>
            discussion_id = @getDiscussionId(el)
            comment = $(@commentSelector, el).first().clone()
            text = @_truncate comment.text().trim(), @commentMaxLength
            comment.text(text)
            if discussion_id
                comment = comment.after(@createReplyLink discussion_id)
            comment

    makeTipTitle: (el) ->
        (api) =>
            comment = $(@commentSelector, el).first()
            title = comment.attr('title')
            (if title then title else 'Commentary')

    createReplyLink: (discussion_id) ->
        $("<a class=\"annotatable-reply\" href=\"javascript:void(0);\" data-discussion-id=\"#{discussion_id}\">See Full Discussion</a>")

    createReturnLink: (discussion_id) ->
        $("<a class=\"annotatable-return\" href=\"javascript:void(0);\" data-discussion-id=\"#{discussion_id}\">Return to annotation</a>")

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

    _truncate: (text = '', limit) ->
        if text.length > limit
            text.substring(0, limit - 1).split(' ').slice(0, -1).join(' ') + '...' # truncate on word boundary
        else
            text
