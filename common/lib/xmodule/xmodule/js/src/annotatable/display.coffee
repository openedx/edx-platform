class @Annotatable
    @_debug: true

    wrapperSelector: '.annotatable-wrapper'
    toggleSelector:  '.annotatable-toggle'
    spanSelector:    '.annotatable-span'
    commentSelector: '.annotatable-comment'
    replySelector:   '.annotatable-reply'
    helpSelector:    '.annotatable-help-icon'
 
    constructor: (el) ->
        console.log 'loaded Annotatable' if @_debug
        @el = el
        @init()

    $: (selector) ->
        $(selector, @el)

    init: () ->
        @initEvents()
        @initTips()

    initEvents: () ->
        @annotationsHidden = false
        @$(@toggleSelector).bind 'click', @onClickToggleAnnotations
        @$(@wrapperSelector).delegate @replySelector, 'click', @onClickReply

    initTips: () ->
        @savedTips = []
        @$(@spanSelector).each (index, el) => $(el).qtip(@getTipOptions el)
        @$(@helpSelector).qtip
            position:
                my: 'right top'
                at: 'bottom left'
                container: @$(@wrapperSelector)
            content:
                title: 'Annotated Reading Help'
                text: "Move your cursor over the highlighted areas to display annotations. 
                       Discuss the annotations in the forums using the link at the
                       bottom of the annotation. You may hide annotations at any time by
                       using the button at the top of the section."
            style:
                classes: 'ui-tooltip-annotatable'

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
            classes: 'ui-tooltip-annotatable ui-tooltip-annotatable-comment'
        events:
            show: @onShowTip

    onShowTip: (event, api) =>
        event.preventDefault() if @annotationsHidden

    onClickToggleAnnotations: (e) =>
        @toggleAnnotations()

    onClickReply: (e) =>
        e.preventDefault()
        anchorEl = @getAnchorByName e.currentTarget
        @scrollTo anchorEl if anchorEl
    
    getAnchorByName: (el) ->
        hash = $(el).attr('href')
        if hash?.charAt(0) == '#'
            name = hash.substr(1)
            anchor = $("a[name='#{name}']").first()
        anchor

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

    scrollTo: (el) ->
        $('html,body').scrollTo(el, {
            duration: 500,
            onAfter: @makeAfterScroll(el)
        })
 
    makeAfterScroll: (el, duration = 2000) ->
        @_once -> el.effect 'highlight', {}, duration

    makeTipContent: (el) ->
        (api) =>
            anchor = $(el).data('discussion-anchor')
            comment = $(@commentSelector, el).first().clone()
            comment = comment.after(@createReplyLink anchor) if anchor
            comment

    makeTipTitle: (el) ->
        (api) =>
            comment = $(@commentSelector, el).first()
            title = comment.attr('title')
            (if title then title else 'Commentary')

    createReplyLink: (anchor) ->
        cls = 'annotatable-reply'
        href = '#' + anchor
        text = 'See Full Discussion'
        $("<a class=\"#{cls}\" href=\"#{href}\">#{text}</a>")

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
