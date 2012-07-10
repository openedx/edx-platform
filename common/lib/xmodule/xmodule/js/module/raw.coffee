class @Raw
    constructor: (@element) ->
        @edit_box = $(".edit-box", @element)
        @preview = $(".preview", @element)
        @edit_box.on('input', =>
            @preview.empty().text(@edit_box.val())
        )

    save: -> @edit_box.val()
