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
            content:
                title: 'Annotated Reading Help'
                text: "To reveal annotations in the reading, click the highlighted areas.
                       Discuss the annotations in the forums using the reply link at the
                       end of the annotation.<br/><br/>
                       To conceal annotations, use the <i>Hide Annotations</i> button."

    getTipOptions: (el) ->
        content:
            title:
                text: @makeTipTitle(el)
                button: 'Close'
            text: @makeTipContent(el)
        position:
            my: 'bottom center' # of tooltip
            at: 'top center' # of target
            target: 'mouse'
            container: @$(@wrapperSelector)
            viewport: true,
            adjust:
                method: 'none shift'
                mouse: false # dont follow the mouse
        show:
            event: 'click'
        hide:
            event: 'click'
        style:
            classes: 'ui-tooltip-annotatable'
        events:
            render: @onRenderTip
            show: @onShowTip

    onRenderTip: (event, api) =>
        $(api.elements.tooltip).draggable
            handle: '.ui-tooltip-title'
            cursor: 'move'

    onShowTip: (event, api) =>
        event.preventDefault() if @annotationsHidden

    onClickToggleAnnotations: (e) =>
        @annotationsHidden = not @annotationsHidden
        @toggleButtonText @annotationsHidden
        @toggleSpans @annotationsHidden
        @toggleTips @annotationsHidden

    onClickReply: (e) =>
        hash = $(e.currentTarget).attr('href')
        if hash?.charAt(0) == '#'
            name = hash.substr(1)
            anchor = $("a[name='#{name}']").first()
            @scrollTo(anchor)

    toggleTips: (hide) ->
        if hide
            @closeAndSaveTips()
        else
            @openSavedTips()

    toggleButtonText: (hide) ->
        buttonText = (if hide then 'Show' else 'Hide')+' Annotations'
        @$(@toggleSelector).text(buttonText)

    toggleSpans: (hide) ->
        @$(@spanSelector).toggleClass 'hide', hide

    scrollTo: (el) ->
        options =
            duration: 500
            onAfter: @_once -> el.effect 'highlight', {}, 2000
        $('html,body').scrollTo(el, options)

    makeTipContent: (el) ->
        (api) =>
            anchor = $(el).data('discussion-anchor')
            comment = $(@commentSelector, el).first().clone()
            comment = comment.after(@createReplyLink(anchor)) if anchor
            comment

    makeTipTitle: (el) ->
        (api) =>
            comment = $(@commentSelector, el).first()
            title = comment.attr('title')
            (if title then title else 'Commentary')
    
    createReplyLink: (anchor) ->
        cls = 'annotatable-reply'
        href = '#' + anchor
        text = 'Reply to this comment'
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
