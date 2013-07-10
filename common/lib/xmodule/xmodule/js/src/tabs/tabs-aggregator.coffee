class @TabsEditorDescriptor
  @isInactiveClass : "is-inactive"
  @tabs_save_functions = {}

  constructor: (element) ->
    @element = element;

    console.log 'hide-settings = ' + @element.find('section.editor').data('hide-header')
    console.log 'element = ', element
    if typeof @element.find('section.editor').data('hide-header') is 'string'
        console.log 'typeof is string'
    if @element.find('section.editor').data('hide-header') is 'True'
      console.log "HIDE ME"
      $('.component-edit-header').hide()
    else
      $('.component-edit-header').show()

    # settingsEditor = @$el.find('.wrapper-comp-settings')
    # editorModeButton =  @$el.find('#editor-mode').find("a")
    # settingsModeButton = @$el.find('#settings-mode').find("a")

    # editorModeButton.removeClass('is-set')
    # settingsEditor.addClass('is-active')
    # settingsModeButton.addClass('is-set')

    @$tabs = $(".tab", @element)
    @$content = $(".component-tab", @element)

    @element.on('click', '.editor-tabs .tab', @onSwitchEditor)

    # If default visible tab is not setted or if were marked as current
    # more than 1 tab just first tab will be shown
    currentTab = @$tabs.filter('.current')
    currentTab = @$tabs.first() if currentTab.length isnt 1
    currentTab.trigger("click", [true])
    @html_id = @$tabs.closest('.wrapper-comp-editor').data('html_id')

   onSwitchEditor: (e, firstTime) =>
    e.preventDefault();

    isInactiveClass = TabsEditorDescriptor.isInactiveClass
    $currentTarget = $(e.currentTarget)

    if not $currentTarget.hasClass('current') or firstTime is true

      previousTab = null

      @$tabs.each( (index, value) ->
        if $(value).hasClass('current')
          previousTab = $(value).html()
      )

      console.log 'previous tab: ' + previousTab

      @$tabs.removeClass('current')
      $currentTarget.addClass('current')

      console.log '$currentTarget = ', $currentTarget

      # Tabs are implemeted like anchors. Therefore we can use hash to find
      # corresponding content
      content_id = $currentTarget.attr('href')

      console.log 'a'

      if $currentTarget.html() is 'Settings'
        console.log 'b'
        settingsEditor = @element.find('.wrapper-comp-settings')
        editorModeButton =  @element.find('#editor-mode').find("a")
        settingsModeButton = @element.find('#settings-mode').find("a")

        @element.find('.launch-latex-compiler').hide()

        editorModeButton.removeClass('is-set')
        settingsEditor.addClass('is-active')
        settingsModeButton.addClass('is-set')
      else
        @element.find('.launch-latex-compiler').show()

      console.log 'c'
      @$content
        .addClass(isInactiveClass)
        .filter(content_id)
        .removeClass(isInactiveClass)

      @$tabs.closest('.wrapper-comp-editor').trigger(
        'TabsEditor:changeTab',
        [
          $currentTarget.text(), # tab_name
          content_id,  # tab_id
          previousTab
        ]
      )


  save: ->
    @element.off('click', '.editor-tabs .tab', @onSwitchEditor)
    # get data from active tab
    tabName = this.$tabs.filter('.current').html()
    if $.isFunction(window.TabsEditorDescriptor['tabs_save_functions'][@html_id][tabName])
      return data: window.TabsEditorDescriptor['tabs_save_functions'][@html_id][tabName]()
    data: null

TabsEditorDescriptor.registerTabCallback = (id, name, callback) ->
  $('#editor-tab-' + id).on 'TabsEditor:changeTab', (e, tab_name, tab_id, previous_tab) ->
    e.stopPropagation()

    callback(previous_tab) if typeof callback is "function" and tab_name is name
