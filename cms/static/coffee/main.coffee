class @CMS
    @setHeight = =>
        windowHeight = $(window).height()
        headerHeight = $('body > header').outerHeight()
        contentHeight = $('.main-content').height()
        @sidebarHeight = if windowHeight > contentHeight then windowHeight - headerHeight else contentHeight - headerHeight
        @minContentHeight = windowHeight - headerHeight

        $('.cal').css('height', @sidebarHeight)
        $('.main-content').css('min-height', @minContentHeight)

    @bind = =>
        $('a.module-edit').click ->
            CMS.edit_item($(this).attr('id'))
            return false
        $(window).bind('resize', CMS.setHeight)

    @edit_item = (id) =>
        $.get('/edit_item', {id: id}, (data) =>
            $('#module-html').empty().append(data)
            CMS.bind()
            CMS.setHeight()
            $('body').addClass('content')
            $('body.content .cal ol > li').css('height','auto')
            $('section.edit-pane').show()
            new Unit('unit-wrapper', id)
        )

$ ->
    $.ajaxSetup
        headers : { 'X-CSRFToken': $.cookie 'csrftoken' }
    $('section.main-content').children().hide()
    $('.editable').inlineEdit()
    $('.editable-textarea').inlineEdit({control: 'textarea'})

    heighest = 0
    $('.cal ol > li').each ->
        heighest = if $(this).height() > heighest then $(this).height() else heighest

    $('.cal ol > li').css('height',heighest + 'px')
    $('body.content .cal ol > li').css('height','auto')

    $('.add-new-section').click -> return false

    $('.new-week .close').click ->
        $(this).parents('.new-week').hide()
        $('p.add-new-week').show()
        return false

    $('.save-update').click ->
        $(this).parent().parent().hide()
        return false

    $('.video-new a').click ->
        $('section.edit-pane').show()
        return false

    $('.problem-new a').click ->
        $('section.edit-pane').show()
        return false

    CMS.setHeight()
    CMS.bind()

