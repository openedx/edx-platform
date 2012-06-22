class @Unit
    constructor: (@element_id, @module_id) ->
        @module = new window[$("##{@element_id}").attr('class')] 'module-html'

        $("##{@element_id} .save-update").click (event) =>
            event.preventDefault()
            $.post("save_item", {
                id: @module_id
                data: JSON.stringify(@module.save())
            })

        $("##{@element_id} .cancel").click (event) =>
            event.preventDefault()
            CMS.edit_item(@module_id)

