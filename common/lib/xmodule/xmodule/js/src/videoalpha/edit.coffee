class @VideoAlphaEditorTabs
  @isInactiveClass : "is-inactive"

  constructor: (element) ->
    @element = element;
    @$tabs = $(".tab", @element)
    @$content = $(".component-tab", @element)

    editBox = $(".edit-box", @element)[0]
    if editBox
      @advanced_editor = CodeMirror.fromTextArea(editBox, {
        mode: "text/html"
        lineNumbers: true
        lineWrapping: true
      })
    @element.on('click', '.editor-tabs .tab', @onSwitchEditor)

   onSwitchEditor: (e) =>
    e.preventDefault();

    isInactiveClass = HTMLEditingDescriptor.isInactiveClass
    $currentTarget = $(e.currentTarget)
    if not $currentTarget.hasClass('current')

      @$tabs.removeClass('current')
      $currentTarget.addClass('current')

      # Tabs are implemeted like anchors. Therefore we can use hash to find corresponding content
      hash = $currentTarget.attr('href')
      @$content
        .addClass(isInactiveClass)
        .filter(hash)
        .removeClass(isInactiveClass)

      if $currentTarget.data('tab') is 'advanced' and @advanced_editor
        @showAdvancedEditor()

  # Show the Advanced (codemirror) Editor. Pulled out as a helper method for unit testing.
  showAdvancedEditor: () ->
    @advanced_editor.focus()

  save: ->
    @element.off('click', '.editor-tabs .tab', @onSwitchEditor)
    data: @advanced_editor.getValue()