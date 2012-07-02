class @Raw
    constructor: (@id) ->
        @edit_box = $("##{@id} .edit-box")
        @preview = $("##{@id} .preview")
        @edit_box.on('input', =>
            @preview.empty().text(@edit_box.val())
        )

    save: -> @edit_box.val()
