class @Annotatable
    @_debug: true
    constructor: (el) ->
        console.log 'loaded Annotatable' if @_debug
        @el = el
        @spandata = $('.annotatable-wrapper', @el).data "spans" 
        @initSpans()

    initSpans: () ->
        selector = 'span.annotatable[data-span-id]'
        $(@el).find(selector).on 'click', (e) => 
            @onClickSpan.call this, e

    onClickSpan: (e) ->
            span_id = e.target.getAttribute('data-span-id')
            discussion_id = @spandata[span_id]
            selector = '.annotatable-discussion[data-discussion-id="'+discussion_id+'"]';
            $discussion = $(selector, @el)
            padding = 20
            top = $discussion.offset().top - padding
            highlighted = false
            complete = () ->
                if !highlighted
                    $discussion.effect('highlight', {}, 1000)
                    highlighted = true

            $('html, body').animate({ 
                scrollTop: top,
            }, 1000, 'swing', complete)
