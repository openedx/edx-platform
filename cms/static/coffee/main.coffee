bind_edit_links = ->
    $('a.module-edit').click ->
        edit_item($(this).attr('id'))
        return false

edit_item = (id) ->
    $.get('/edit_item', {id: id}, (data) ->
        $('#module-html').empty().append(data)
        bind_edit_links()
        $('section.edit-pane').show()
        $('body').addClass('content')
        window['construct_html']('module-html')
    )

$ ->
    $('section.main-content').children().hide()
    $('.editable').inlineEdit()
    $('.editable-textarea').inlineEdit({control: 'textarea'})

    heighest = 0
    $('.cal ol > li').each ->
        heighest = if $(this).height() > heighest then $(this).height() else heighest

    $('.cal ol > li').css('height',heighest + 'px')

    $('.add-new-section').click -> return false

    $('.new-week .close').click ->
        $(this).parents('.new-week').hide()
        $('p.add-new-week').show()
        return false

    $('.save-update').click ->
        $(this).parent().parent().hide()
        return false


    setHeight = ->
        windowHeight = $(this).height()
        contentHeight = windowHeight - 29

        $('section.main-content > section').css('min-height', contentHeight)
        $('body.content .cal').css('height', contentHeight)

        $('.edit-week').click ->
            $('body').addClass('content')
            $('body.content .cal').css('height', contentHeight)
            $('section.edit-pane').show()
            return false

        $('a.week-edit').click ->
            $('body').addClass('content')
            $('body.content .cal').css('height', contentHeight)
            $('section.edit-pane').show()
            return false

        $('a.sequence-edit').click ->
            $('body').addClass('content')
            $('body.content .cal').css('height', contentHeight)
            $('section.edit-pane').show()
            return false

    $(document).ready(setHeight)
    $(window).bind('resize', setHeight)

    $('.video-new a').click ->
        $('section.edit-pane').show()
        return false

    $('.problem-new a').click ->
        $('section.edit-pane').show()
        return false

    bind_edit_links()

