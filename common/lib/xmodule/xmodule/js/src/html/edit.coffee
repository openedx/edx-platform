class @HTMLEditingDescriptor
  @isInactiveClass : "is-inactive"

  constructor: (element) ->
    @element = element;

    @advanced_editor = CodeMirror.fromTextArea($(".edit-box", @element)[0], {
      mode: "text/html"
      lineNumbers: true
      lineWrapping: true
    })

    @$advancedEditorWrapper = $(@advanced_editor.getWrapperElement())
    @$advancedEditorWrapper.addClass(HTMLEditingDescriptor.isInactiveClass)

#   This is a workaround for the fact that tinyMCE's baseURL property is not getting correctly set on AWS
#   instances (like sandbox). It is not necessary to explicitly set baseURL when running locally.
    tinyMCE.baseURL = '/static/js/vendor/tiny_mce'
    @tiny_mce_textarea = $(".tiny-mce", @element).tinymce({
      script_url : '/static/js/vendor/tiny_mce/tiny_mce.js',
      theme : "advanced",
      skin: 'studio',
      schema: "html5",
      # Necessary to preserve relative URLs to our images.
      convert_urls : false,
      # TODO: we should share this CSS with studio (and LMS)
      content_css : "/static/css/tiny-mce.css",
      formats : {
        # Disable h4, h5, and h6 styles as we don't have CSS for them.
        h4: {},
        h5: {},
        h6: {},
        # tinyMCE does block level for code by default
        code: {inline: 'code'}
      },
      # Disable visual aid on borderless table.
      visual:false,
      # We may want to add "styleselect" when we collect all styles used throughout the LMS
      theme_advanced_buttons1 : "formatselect,bold,italic,underline,|,bullist,numlist,outdent,indent,|,blockquote,wrapAsCode,|,link,unlink",
      theme_advanced_toolbar_location : "top",
      theme_advanced_toolbar_align : "left",
      theme_advanced_statusbar_location : "none",
      theme_advanced_resizing : true,
      theme_advanced_blockformats : "p,pre,h1,h2,h3",
      width: '100%',
      height: '400px',
      setup : @setupTinyMCE,
      # Cannot get access to tinyMCE Editor instance (for focusing) until after it is rendered.
      # The tinyMCE callback passes in the editor as a paramter.
      init_instance_callback: @focusVisualEditor
    })

    @showingVisualEditor = true
    # Doing these find operations within onSwitchEditor leads to sporadic failures on Chrome (version 20 and older).
    $element = $(element)
    @$htmlTab = $element.find('.html-tab')
    @$visualTab = $element.find('.visual-tab')

    @element.on('click', '.editor-tabs .tab', @onSwitchEditor)

  setupTinyMCE: (ed) =>
    ed.addButton('wrapAsCode', {
      title : 'Code',
      image : '/static/images/ico-tinymce-code.png',
      onclick : () ->
        ed.formatter.toggle('code')
        # Without this, the dirty flag does not get set unless the user also types in text.
        # Visual Editor must be marked as dirty or else we won't populate the Advanced Editor from it.
        ed.isNotDirty = false
    })

    ed.onNodeChange.add((editor, command, e) ->
      command.setActive('wrapAsCode', e.nodeName == 'CODE')
    )

    @visualEditor = ed

  onSwitchEditor: (e) =>
    e.preventDefault();

    $currentTarget = $(e.currentTarget)
    if not $currentTarget.hasClass('current')
      $currentTarget.addClass('current')
      @$mceToolbar.toggleClass(HTMLEditingDescriptor.isInactiveClass)
      @$advancedEditorWrapper.toggleClass(HTMLEditingDescriptor.isInactiveClass)

      visualEditor = @getVisualEditor()
      if $currentTarget.data('tab') is 'visual'
        @$htmlTab.removeClass('current')
        @showVisualEditor(visualEditor)
      else
        @$visualTab.removeClass('current')
        @showAdvancedEditor(visualEditor)

  # Show the Advanced (codemirror) Editor. Pulled out as a helper method for unit testing.
  showAdvancedEditor: (visualEditor) ->
    if visualEditor.isDirty()
      @advanced_editor.setValue(visualEditor.getContent({no_events: 1}))
      @advanced_editor.setCursor(0)
    @advanced_editor.refresh()
    @advanced_editor.focus()
    @showingVisualEditor = false

  # Show the Visual (tinyMCE) Editor. Pulled out as a helper method for unit testing.
  showVisualEditor: (visualEditor) ->
    visualEditor.setContent(@advanced_editor.getValue())
    # In order for isDirty() to return true ONLY if edits have been made after setting the text,
    # both the startContent must be sync'ed up and the dirty flag set to false.
    visualEditor.startContent = visualEditor.getContent({format: "raw", no_events: 1});
    @focusVisualEditor(visualEditor)
    @showingVisualEditor = true

  focusVisualEditor: (visualEditor) =>
    visualEditor.focus()
    # Need to mark editor as not dirty both when it is initially created and when we switch back to it.
    visualEditor.isNotDirty = true
    if not @$mceToolbar?
      @$mceToolbar = $(@element).find('table.mceToolbar')

  getVisualEditor: () ->
    ###
    Returns the instance of TinyMCE.
    This is different from the textarea that exists in the HTML template (@tiny_mce_textarea.

    Pulled out as a helper method for unit test.
    ###
    return @visualEditor

  save: ->
    @element.off('click', '.editor-tabs .tab', @onSwitchEditor)
    text = @advanced_editor.getValue()
    visualEditor = @getVisualEditor()
    if @showingVisualEditor and visualEditor.isDirty()
      text = visualEditor.getContent({no_events: 1})
    data: text
