class @Annotatable
    constructor: (el) ->
        console.log "loaded Annotatable"
        $(el).find(".annotatable").on "click", (e) ->
            data = $(".annotatable-wrapper", el).data("spans")
            span_id = e.target.getAttribute("data-span-id")
            msg = "annotatable span clicked. discuss span [" + span_id + "] in discussion [" + data[span_id] + "]"
            console.log data
            window.alert msg
