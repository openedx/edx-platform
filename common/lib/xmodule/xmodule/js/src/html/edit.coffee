class @HTMLEditingDescriptor
  @isInactiveClass : "is-inactive"

  constructor: (element) ->
    @element = element;
    @base_asset_url = @element.find("#editor-tab").data('base-asset-url')
    if @base_asset_url == undefined
      @base_asset_url = null

    @advanced_editor = CodeMirror.fromTextArea($(".edit-box", @element)[0], {
      mode: "text/html"
      lineNumbers: true
      lineWrapping: true
    })

    @$advancedEditorWrapper = $(@advanced_editor.getWrapperElement())
    @$advancedEditorWrapper.addClass(HTMLEditingDescriptor.isInactiveClass)

#   This is a workaround for the fact that tinyMCE's baseURL property is not getting correctly set on AWS
#   instances (like sandbox). It is not necessary to explicitly set baseURL when running locally.
    tinyMCE.baseURL = "#{baseUrl}/js/vendor/tiny_mce"
#   This is necessary for the LMS bulk e-mail acceptance test. In that particular scenario,
#   tinyMCE incorrectly decides that the suffix should be "", which means it fails to load files.
    tinyMCE.suffix = ".min"
    @tiny_mce_textarea = $(".tiny-mce", @element).tinymce({
      script_url : "#{baseUrl}/js/vendor/tiny_mce/tiny_mce.min.js",
      theme : "modern",
      skin: 'studio-tmce4',
      schema: "html5",
      # Necessary to preserve relative URLs to our images.
      convert_urls : false,
      # TODO: we should share this CSS with studio (and LMS)
      content_css : "#{baseUrl}/css/tiny-mce.css",
      formats : {
      # Disable h4, h5, and h6 styles as we don't have CSS for them.
      # TODO: this doesn't seem to be working with the upgrade.
        h4: {},
        h5: {},
        h6: {},
      # tinyMCE does block level for code by default
        code: {inline: 'code'}
      },
      # Disable visual aid on borderless table.
      visual: false,
      plugins: "textcolor, link, image, codemirror",
      codemirror: {
        path: "#{baseUrl}/js/vendor/CodeMirror"
      },
      # We may want to add "styleselect" when we collect all styles used throughout the LMS
      # Can have a single toolbar by just specifying "toolbar". Splitting for now so all are visible.
      toolbar1: "formatselect | fontselect | bold italic underline forecolor | bullist numlist outdent indent",
      toolbar2: "link unlink image | blockquote wrapAsCode code",
      # TODO: i18n
      block_formats: "Paragraph=p;Preformatted=pre;Heading 1=h1;Heading 2=h2;Heading 3=h3",
      width: '100%',
      height: '400px',
      menubar: false,
      statusbar: false,
      setup: @setupTinyMCE,
      # Cannot get access to tinyMCE Editor instance (for focusing) until after it is rendered.
      # The tinyMCE callback passes in the editor as a paramter.
      init_instance_callback: @initInstanceCallback
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
      image : "#{baseUrl}/images/ico-tinymce-code.png",
      onclick : () ->
        ed.formatter.toggle('code')
        # Without this, the dirty flag does not get set unless the user also types in text.
        # Visual Editor must be marked as dirty or else we won't populate the Advanced Editor from it.
        ed.isNotDirty = false
    })

    @visualEditor = ed

    ed.on('change', @changeHandler)

  # Intended to run after the "image" plugin is used so that static urls are set
  # correctly in the Visual editor immediately after command use.
  changeHandler: (e) =>
    # The fact that we have to listen to all change events and act on an event actually fired
    # from undo (which is where the "level" comes from) is extremely ugly. However, plugins
    # don't fire any events in TinyMCE version 4 that I can hook into (in particular, not ExecCommand).
    if e.level and e.level.content and e.level.content.match(/<img src="\/static\//)
      content = rewriteStaticLinks(e.target.getContent(), '/static/', @base_asset_url)
      e.target.setContent(content)

  onSwitchEditor: (e) =>
    e.preventDefault();

    $currentTarget = $(e.currentTarget)
    if not $currentTarget.hasClass('current')
      $currentTarget.addClass('current')

      # Initializing $mceToolbar if undefined.
      if not @$mceToolbar?
        @$mceToolbar = $(@element).find('table.mceToolbar')
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
      content = rewriteStaticLinks(visualEditor.getContent({no_events: 1}), @base_asset_url, '/static/')
      @advanced_editor.setValue(content)
      @advanced_editor.setCursor(0)
    @advanced_editor.refresh()
    @advanced_editor.focus()
    @showingVisualEditor = false

  # Show the Visual (tinyMCE) Editor. Pulled out as a helper method for unit testing.
  showVisualEditor: (visualEditor) ->
    # In order for isDirty() to return true ONLY if edits have been made after setting the text,
    # both the startContent must be sync'ed up and the dirty flag set to false.
    content = rewriteStaticLinks(@advanced_editor.getValue(), '/static/', @base_asset_url)
    visualEditor.setContent(content)
    visualEditor.startContent = visualEditor.getContent({format : 'raw'})
    @focusVisualEditor(visualEditor)
    @showingVisualEditor = true

  initInstanceCallback: (visualEditor) =>
    visualEditor.setContent(rewriteStaticLinks(@advanced_editor.getValue(), '/static/', @base_asset_url))
    @focusVisualEditor(visualEditor)

  focusVisualEditor: (visualEditor) =>
    visualEditor.focus()
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
      text = rewriteStaticLinks(visualEditor.getContent({no_events: 1}), @base_asset_url, '/static/')
    data: text
