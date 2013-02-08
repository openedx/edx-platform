class @Annotatable
    @_debug: true

    wrapperSelector: '.annotatable-wrapper'
    toggleSelector: '.annotatable-toggle'
    spanSelector: 'span.annotatable'
    commentSelector: '.annotatable-comment'
    replySelector: 'a.annotatable-reply'
 
    constructor: (el) ->
        console.log 'loaded Annotatable' if @_debug
        @init(el)

    $: (selector) ->
        $(selector, @el)

    init: (el) ->
        @el = el
        @hideAnnotations = false
        @initEvents()
        @initToolTips()

    initEvents: () ->
        @$(@toggleSelector).bind 'click', @onClickToggleAnnotations
        @$(@wrapperSelector).delegate @replySelector, 'click', @onClickReply
            
    initToolTips: () ->
        @$(@spanSelector).each (index, el) =>
            $(el).qtip(@getTipOptions el)

    getTipOptions: (el) ->
        content:
            title: 
                text: @makeTipTitle(el)
                button: 'Close'
            text: @makeTipComment(el)
        position:
            my: 'bottom center' # of tooltip
            at: 'top center' # of target
            target: 'mouse'
            container: @$(@wrapperSelector)
            adjust: 
                mouse: false # dont follow the mouse
                method: 'shift none'
        show: 
            event: 'click'
        hide:
            event: 'click'
        style:
            classes: 'ui-tooltip-annotatable'
        events:
            show: @onShowTipComment

    onShowTipComment: (event, api) =>
        event.preventDefault() if @hideAnnotations

    onClickToggleAnnotations: (e) =>
        @hideAnnotations = !@hideAnnotations
        hide = @hideAnnotations

        @hideAllTips() if hide
        @$(@spanSelector).toggleClass('hide', hide)
        @$(@toggleSelector).text((if hide then 'Show' else 'Hide') + ' Annotations')

    onClickReply: (e) =>
        hash = $(e.currentTarget).attr('href')
        if hash?.charAt(0) == '#'
            name = hash.substr(1)
            anchor = $("a[name='#{name}']").first()
            @scrollTo(anchor) if anchor.length == 1

    scrollTo: (el, padding = 20) ->
        scrollTop = el.offset().top - padding
        $('html,body').animate(scrollTop: scrollTop, 500, 'swing')

    makeTipComment: (el) ->
        return (api) =>
            comment = $(@commentSelector, el).first().clone()
            anchor = $(el).data('discussion-anchor')
            if anchor
                comment.append(@createReplyLink(anchor))
            comment.contents()

    makeTipTitle: (el) ->
        return (api) =>
            comment = $(@commentSelector, el).first()
            title = comment.attr('title')
            (if title then title else 'Commentary')
    
    createReplyLink: (anchor) ->
        $("<a class=\"annotatable-reply\" href=\"##{anchor}\">Reply to Comment</a>")
    
    hideAllTips: () ->
        @$(@spanSelector).each (index, el) -> $(el).qtip('api').hide()