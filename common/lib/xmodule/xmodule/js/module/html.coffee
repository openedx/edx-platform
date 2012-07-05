class @HTML
    constructor: (@element) ->
        @edit_box = $(".edit-box", @element)
        @preview = $(".preview", @element)
        @edit_box.on('input', =>
            @preview.empty().append(@edit_box.val())
        )

    save: -> {text: @edit_box.val()}
