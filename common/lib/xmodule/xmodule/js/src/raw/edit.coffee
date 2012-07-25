class @RawDescriptor
    constructor: (@element) ->
        @edit_box = $(".edit-box", @element)

    save: -> @edit_box.val()
