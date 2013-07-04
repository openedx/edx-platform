class @TabsEditorDescriptor
  @isInactiveClass : "is-inactive"

  constructor: (element) ->
    @element = element;
    @$tabs = $(".tab", @element)
    @$content = $(".component-tab", @element)

    @element.on('click', '.editor-tabs .tab', @onSwitchEditor)

    # If default visible tab is not setted or if were marked as current
    # more than 1 tab just first tab will be shown
    currentTab = @$tabs.filter('.current')
    currentTab = @$tabs.first() if currentTab.length isnt 1
    currentTab.trigger("click", [true])

   onSwitchEditor: (e, reset) =>
    e.preventDefault();

    isInactiveClass = TabsEditorDescriptor.isInactiveClass
    $currentTarget = $(e.currentTarget)

    if not $currentTarget.hasClass('current') or reset is true

      @$tabs.removeClass('current')
      $currentTarget.addClass('current')

      # Tabs are implemeted like anchors. Therefore we can use hash to find
      # corresponding content
      content_id = $currentTarget.attr('href')

      @$content
        .addClass(isInactiveClass)
        .filter(content_id)
        .removeClass(isInactiveClass)

      @$tabs.closest('.wrapper-comp-editor').trigger(
        'TabsEditor:changeTab',
        [
          $currentTarget.text(), # tab_name
          content_id  # tab_id
        ]
      )

  save: ->
    @element.off('click', '.editor-tabs .tab', @onSwitchEditor)
    # Link to instance of CodeMirror is stored in data attribute of DOM element
    # If it exist we retreive the data from CodeMirror
    advanced_editor = $('.edit-box', @element).first().data('CodeMirror')
    if advanced_editor
      text = advanced_editor.getValue()
      data: text

window.TabsEditorDescriptor = window.TabsEditorDescriptor || {};
TabsEditorDescriptor.registerTabCallback = (id, name, callback) ->
  $('#editor-tab-' + id).on 'TabsEditor:changeTab', (e, tab_name, tab_id) ->
    e.stopPropagation()
    callback() if typeof callback is "function" and tab_name is name

