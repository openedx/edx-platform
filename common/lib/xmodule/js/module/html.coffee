class @HTML
    constructor: (@id) ->
        id = @id
        $("##{id} .edit-box").on('input', ->
            $("##{id} .preview").empty().append($(this).val())
        )

    save: -> $("##{@id} .edit-box").val()
