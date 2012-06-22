class @HTML
    constructor: (id) ->
        $('#' + id + " #edit-box").on('input', ->
            $('#' + id + ' #edit-preview').empty().append($(this).val())
        )
