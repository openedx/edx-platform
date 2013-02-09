class @Annotatable
    @_debug: true

    wrapperSelector: '.annotatable-wrapper'
    toggleSelector: '.annotatable-toggle'
    spanSelector: '.annotatable-span'
    commentSelector: '.annotatable-comment'
    replySelector: '.annotatable-reply'
    helpSelector: '.annotatable-help-icon'
 
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
        @visibleTips = []
        @$(@spanSelector).each (index, el) =>
            $(el).qtip(@getTipOptions el)

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
        toggle = @$(@toggleSelector)
        spans = @$(@spanSelector)

        @annotationsHidden = !@annotationsHidden
        if @annotationsHidden
            spans.toggleClass('hide', true)
            toggle.text('Show Annotations')
            @visibleTips = @getVisibleTips()
            @hideTips(@visibleTips)
        else
            spans.toggleClass('hide', false)
            toggle.text('Hide Annotations')
            @showTips(@visibleTips)

    onClickReply: (e) =>
        hash = $(e.currentTarget).attr('href')
        if hash?.charAt(0) == '#'
            name = hash.substr(1)
            anchor = $("a[name='#{name}']").first()
            @scrollTo(anchor) if anchor.length == 1

    scrollTo: (el, padding = 20) ->
        props =
            scrollTop: (el.offset().top - padding)
        opts =
            duration: 500
            complete: @_once -> el.effect 'highlight', {}, 2000

        $('html,body').animate(props, opts)

    makeTipContent: (el) ->
        (api) =>
            comment = $(@commentSelector, el).first().clone()
            anchor = $(el).data('discussion-anchor')
            if anchor
                comment.append(@createReplyLink(anchor))
            comment.contents()

    makeTipTitle: (el) ->
        (api) =>
            comment = $(@commentSelector, el).first()
            title = comment.attr('title')
            (if title then title else 'Commentary')
    
    createReplyLink: (anchor) ->
        $("<a class=\"annotatable-reply\" href=\"##{anchor}\">Reply to this comment</a>")

    getVisibleTips: () ->
        visible = []
        @$(@spanSelector).each (index, el) ->
            api = $(el).qtip('api')
            tip = $(api?.elements.tooltip)
            if tip.is(':visible')
                visible.push [el, tip.offset()]
        visible
    
    hideTips: (items) ->
        elements = (pair[0] for pair in items)
        $(elements).qtip('hide')

    showTips: (items) ->
        $.each items, (index, item) ->
            [el, offset] = item
            api = $(el).qtip('api')
            api?.show()
            $(api?.elements.tooltip).offset(offset)
 
    _once: (fn) ->
        done = false
        return =>
            fn.call this unless done
            done = true
