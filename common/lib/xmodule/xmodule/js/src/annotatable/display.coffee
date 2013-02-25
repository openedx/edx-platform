class @Annotatable
    _debug: false

    wrapperSelector:            '.annotatable-wrapper'
    toggleAnnotationsSelector:  '.annotatable-toggle-annotations'
    toggleInstructionsSelector: '.annotatable-toggle-instructions'
    instructionsSelector:       '.annotatable-instructions'
    spanSelector:               '.annotatable-span'
    replySelector:              '.annotatable-reply'

    problemXModuleSelector:     '.xmodule_CapaModule'
    problemSelector:            'section.problem'
    problemInputSelector:       'section.problem .annotation-input'
    problemReturnSelector:      'section.problem .annotation-return'

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
        # For handling hide/show of annotations and instructions
        @annotationsHidden = false
        @$(@toggleAnnotationsSelector).bind 'click', @onClickToggleAnnotations

        @instructionsHidden = false
        @$(@toggleInstructionsSelector).bind 'click', @onClickToggleInstructions

        # For handling 'reply to annotation' events that scroll to the associated capa problem.
        # These are contained in the tooltips, which should be rendered somewhere in the wrapper
        # (see the qtip2 options, this must be set explicitly, otherwise they render in the body).
        @$(@wrapperSelector).delegate @replySelector, 'click', @onClickReply

        # For handling 'return to annotation' events from capa problems. Assumes that:
        #   1) There are annotationinput capa problems rendered on the page
        #   2) Each one has an embedded "return to annotation" link (from the capa problem template).
        # The capa problem's html is injected via AJAX so this just sets a listener on the body and
        # handles the click event there.
        $('body').delegate @problemReturnSelector, 'click', @onClickReturn
  
    initTips: () ->
        @savedTips = []
        @$(@spanSelector).each (index, el) =>
            $(el).qtip(@getTipOptions el)

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

    onShowTip: (event, api) => event.preventDefault() if @annotationsHidden

    onClickToggleAnnotations: (e) => @toggleAnnotations()

    onClickToggleInstructions: (e) => @toggleInstructions()

    onClickReply: (e) => @replyTo(e.currentTarget)

    onClickReturn: (e) => @returnFrom(e.currentTarget)

    getSpanForProblemReturn: (el) ->
        problem_id = $(@problemReturnSelector).index(el)
        @$(@spanSelector).filter("[data-problem-id='#{problem_id}']")

    getProblem: (el) ->
        problem_id = @getProblemId(el)
        $(@problemSelector).has(@problemInputSelector).eq(problem_id)

    getProblemId: (el) ->
        $(el).data('problem-id')

    toggleAnnotations: () ->
        hide = (@annotationsHidden = not @annotationsHidden)
        @toggleAnnotationButtonText hide
        @toggleSpans hide
        @toggleTips hide

    toggleTips: (hide) ->
        if hide then @closeAndSaveTips() else @openSavedTips()

    toggleAnnotationButtonText: (hide) ->
        buttonText = (if hide then 'Show' else 'Hide')+' Annotations'
        @$(@toggleAnnotationsSelector).text(buttonText)

    toggleInstructions: () ->
      hide = (@instructionsHidden = not @instructionsHidden)
      @toggleInstructionsButtonText hide
      @toggleInstructionsText hide

    toggleInstructionsButtonText: (hide) ->
        buttonText = (if hide then 'Show' else 'Hide')+' Instructions'
        @$(@toggleInstructionsSelector).text(buttonText)

    toggleInstructionsText: (hide) ->
        @$(@instructionsSelector)[if hide then 'slideUp' else 'slideDown']()

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
        span_el.effect 'highlight', {color: 'rgba(0,0,0,0.5)' }, 1000

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
            (if title then title else 'Commentary')

    createComment: (text) ->
        $("<div class=\"annotatable-comment\">#{text}</div>")

    createReplyLink: (problem_id) ->
        $("<a class=\"annotatable-reply\" href=\"javascript:void(0);\" data-problem-id=\"#{problem_id}\">Reply to Annotation</a>")

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
