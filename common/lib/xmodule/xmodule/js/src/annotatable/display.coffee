class @Annotatable
    _debug: false

    # selectors for the annotatable xmodule
    wrapperSelector:            '.annotatable-wrapper'
    toggleAnnotationsSelector:  '.annotatable-toggle-annotations'
    toggleInstructionsSelector: '.annotatable-toggle-instructions'
    instructionsSelector:       '.annotatable-instructions'
    sectionSelector:            '.annotatable-section'
    spanSelector:               '.annotatable-span'
    replySelector:              '.annotatable-reply'

    # these selectors are for responding to events from the annotation capa problem type
    problemXModuleSelector:     '.xmodule_CapaModule'
    problemSelector:            'div.problem'
    problemInputSelector:       'div.problem .annotation-input'
    problemReturnSelector:      'div.problem .annotation-return'

    constructor: (el) ->
        console.log 'loaded Annotatable' if @_debug
        @el = el
        @$el = $(el)
        @init()

    $: (selector) ->
        $(selector, @el)

    init: () ->
        @initEvents()
        @initTips()

    initEvents: () ->
        # Initialize toggle handlers for the instructions and annotations sections
        [@annotationsHidden, @instructionsHidden] = [false, false]
        @$(@toggleAnnotationsSelector).bind 'click', @onClickToggleAnnotations
        @$(@toggleInstructionsSelector).bind 'click', @onClickToggleInstructions

        # Initialize handler for 'reply to annotation' events that scroll to
        # the associated problem. The reply buttons are part of the tooltip
        # content. It's important that the tooltips be configured to render
        # as descendants of the annotation module and *not* the document.body.
        @$el.on 'click', @replySelector, @onClickReply

        # Initialize handler for 'return to annotation' events triggered from problems.
        #   1) There are annotationinput capa problems rendered on the page
        #   2) Each one has an embedded return link (see annotation capa problem template).
        # Since the capa problem injects HTML content via AJAX, the best we can do is
        # is let the click events bubble up to the body and handle them there.
        $(document).on 'click', @problemReturnSelector, @onClickReturn

    initTips: () ->
        # tooltips are used to display annotations for highlighted text spans
        @$(@spanSelector).each (index, el) =>
            $(el).qtip(@getSpanTipOptions el)

    getSpanTipOptions: (el) ->
        content:
            title:
                text: @makeTipTitle(el)
            text: @makeTipContent(el)
        position:
            my: 'bottom center' # of tooltip
            at: 'top center' # of target
            target: $(el) # where the tooltip was triggered (i.e. the annotation span)
            container: @$(@wrapperSelector)
            adjust:
                y: -5
        show:
            event: 'click mouseenter'
            solo: true
        hide:
            event: 'click mouseleave'
            delay: 500,
            fixed: true # don't hide the tooltip if it is moused over
        style:
            classes: 'ui-tooltip-annotatable'
        events:
            show: @onShowTip
            move: @onMoveTip

    onClickToggleAnnotations: (e) => @toggleAnnotations()

    onClickToggleInstructions: (e) => @toggleInstructions()

    onClickReply: (e) => @replyTo(e.currentTarget)

    onClickReturn: (e) => @returnFrom(e.currentTarget)

    onShowTip: (event, api) =>
        event.preventDefault() if @annotationsHidden

    onMoveTip: (event, api, position) =>
        ###
        This method handles a vertical positioning bug in Firefox as
        well as an edge case in which a tooltip is displayed above a
        non-overlapping span like this:

                             (( TOOLTIP ))
                                  \/
        text text text ... text text text ...... <span span span>
        <span span span>

        The problem is that the tooltip looks disconnected from both spans, so
        we should re-position the tooltip to appear above the span.
        ###

        tip = api.elements.tooltip
        adjust_y = api.options.position?.adjust?.y || 0
        container = api.options.position?.container || $('body')
        target = api.elements.target

        rects = $(target).get(0).getClientRects()
        is_non_overlapping = (rects?.length == 2 and rects[0].left > rects[1].right)

        if is_non_overlapping
            # we want to choose the largest of the two non-overlapping spans and display
            # the tooltip above the center of it (see api.options.position settings)
            focus_rect = (if rects[0].width > rects[1].width then rects[0] else rects[1])
        else
            # always compute the new position because Firefox doesn't
            # properly vertically position the tooltip
            focus_rect = rects[0]

        rect_center = focus_rect.left + (focus_rect.width / 2)
        rect_top = focus_rect.top
        tip_width = $(tip).width()
        tip_height = $(tip).height()

        # tooltip is positioned relative to its container, so we need to factor in offsets
        container_offset = $(container).offset()
        offset_left = -container_offset.left
        offset_top = $(document).scrollTop() - container_offset.top

        tip_left = offset_left + rect_center - (tip_width / 2)
        tip_top =  offset_top + rect_top - tip_height + adjust_y

        # make sure the new tip position doesn't clip the edges of the screen
        win_width = $(window).width()
        if tip_left < offset_left
            tip_left = offset_left
        else if tip_left + tip_width > win_width + offset_left
            tip_left = win_width + offset_left - tip_width

        # final step: update the position object (used by qtip2 to show the tip after the move event)
        $.extend position, 'left': tip_left, 'top': tip_top

    getSpanForProblemReturn: (el) ->
        problem_id = $(@problemReturnSelector).index(el)
        @$(@spanSelector).filter("[data-problem-id='#{problem_id}']")

    getProblem: (el) ->
        problem_id = @getProblemId(el)
        $(@problemInputSelector).eq(problem_id)

    getProblemId: (el) ->
        $(el).data('problem-id')

    toggleAnnotations: () ->
        hide = (@annotationsHidden = not @annotationsHidden)
        @toggleAnnotationButtonText hide
        @toggleSpans hide
        @toggleTips hide

    toggleTips: (hide) ->
        visible = @findVisibleTips()
        @hideTips visible

    toggleAnnotationButtonText: (hide) ->
        if hide
            buttonText = gettext('Show Annotations')
        else
            buttonText = gettext('Hide Annotations')
        @$(@toggleAnnotationsSelector).text(buttonText)

    toggleInstructions: () ->
      hide = (@instructionsHidden = not @instructionsHidden)
      @toggleInstructionsButton hide
      @toggleInstructionsText hide

    toggleInstructionsButton: (hide) ->
        if hide
            txt = gettext('Expand Instructions')
        else
            txt = gettext('Collapse Instructions')
        cls = (if hide then ['expanded', 'collapsed'] else ['collapsed','expanded'])
        @$(@toggleInstructionsSelector).text(txt).removeClass(cls[0]).addClass(cls[1])

    toggleInstructionsText: (hide) ->
        slideMethod = (if hide then 'slideUp' else 'slideDown')
        @$(@instructionsSelector)[slideMethod]()

    toggleSpans: (hide) ->
        @$(@spanSelector).toggleClass 'hide', hide, 250

    replyTo: (buttonEl) ->
      offset = -20
      el = @getProblem buttonEl
      if el.length > 0
        @scrollTo(el, @afterScrollToProblem, offset)
      else
        console.log('problem not found. event: ', e) if @_debug

    returnFrom: (buttonEl) ->
      offset = -200
      el = @getSpanForProblemReturn buttonEl
      if el.length > 0
        @scrollTo(el, @afterScrollToSpan, offset)
      else
        console.log('span not found. event:', e) if @_debug

    scrollTo: (el, after, offset = -20) ->
        $('html,body').scrollTo(el, {
            duration: 500
            onAfter: @_once => after?.call this, el
            offset: offset
        }) if $(el).length > 0

    afterScrollToProblem: (problem_el) ->
        problem_el.effect 'highlight', {}, 500

    afterScrollToSpan: (span_el) ->
        span_el.addClass 'selected', 400, 'swing', ->
            span_el.removeClass 'selected', 400, 'swing'

    makeTipContent: (el) ->
        (api) =>
            text = $(el).data('comment-body')
            comment = @createComment(text)
            problem_id = @getProblemId(el)
            reply = @createReplyLink(problem_id)
            $(comment).add(reply)

    makeTipTitle: (el) ->
        (api) =>
            title = $(el).data('comment-title')
            (if title then title else gettext('Commentary'))

    createComment: (text) ->
        $("<div class=\"annotatable-comment\">#{text}</div>")

    createReplyLink: (problem_id) ->
        linktxt = gettext('Reply to Annotation')
        $("<a class=\"annotatable-reply\" href=\"javascript:void(0);\" data-problem-id=\"#{problem_id}\">#{linktxt}</a>")

    findVisibleTips: () ->
        visible = []
        @$(@spanSelector).each (index, el) ->
            api = $(el).qtip('api')
            tip = $(api?.elements.tooltip)
            if tip.is(':visible')
                visible.push el
        visible

    hideTips: (elements) ->
        $(elements).qtip('hide')

    _once: (fn) ->
        done = false
        return =>
            fn.call this unless done
            done = true
