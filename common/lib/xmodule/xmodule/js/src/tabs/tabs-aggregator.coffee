class @TabsEditorDescriptor
  @isInactiveClass : "is-inactive"
  @tabs_save_functions = {}

  constructor: (element) ->
    @element = element;

    if @element.find('section.editor-with-tabs').data('hide-header') is 'True'
      $('.component-edit-header').hide()
    else
      $('.component-edit-header').show()

    @$tabs = $(".tab", @element)
    @$content = $(".component-tab", @element)

    @element.find('.editor-tabs .tab').each (index, value) =>
      $(value).on('click', @onSwitchEditor)

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

      @$tabs.removeClass('current')
      $currentTarget.addClass('current')

      # Tabs are implemeted like anchors. Therefore we can use hash to find
      # corresponding content
      content_id = $currentTarget.attr('href')

      # Settings tab name is hardcoded!
      if $currentTarget.html() is 'Settings'
        settingsEditor = @element.find('.wrapper-comp-settings')
        editorModeButton =  @element.find('#editor-mode').find("a")
        settingsModeButton = @element.find('#settings-mode').find("a")

        @element.find('.launch-latex-compiler').hide()

        editorModeButton.removeClass('is-set')
        settingsEditor.addClass('is-active')
        settingsModeButton.addClass('is-set')
      else
        @element.find('.launch-latex-compiler').show()

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
    tabName = @$tabs.filter('.current').html()
    if $.isFunction(window.TabsEditorDescriptor['tabs_save_functions'][@html_id][tabName])
      return data: window.TabsEditorDescriptor['tabs_save_functions'][@html_id][tabName]()
    data: null

TabsEditorDescriptor.registerTabCallback = (id, name, callback) ->
  $('#editor-tab-' + id).on 'TabsEditor:changeTab', (e, tab_name, tab_id, previous_tab) ->
    e.stopPropagation()

    callback(previous_tab) if typeof callback is "function" and tab_name is name
