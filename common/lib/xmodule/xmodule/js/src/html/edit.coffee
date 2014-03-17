class @HTMLEditingDescriptor
  @isInactiveClass : "is-inactive"

  constructor: (element) ->
    @element = element;
    @base_asset_url = @element.find("#editor-tab").data('base-asset-url')
    if @base_asset_url == undefined
      @base_asset_url = null

#   This is a workaround for the fact that tinyMCE's baseURL property is not getting correctly set on AWS
#   instances (like sandbox). It is not necessary to explicitly set baseURL when running locally.
    tinyMCE.baseURL = "#{baseUrl}/js/vendor/tiny_mce"
#   This is necessary for the LMS bulk e-mail acceptance test. In that particular scenario,
#   tinyMCE incorrectly decides that the suffix should be "", which means it fails to load files.
    tinyMCE.suffix = ".min"
    @tiny_mce_textarea = $(".tiny-mce", @element).tinymce({
      script_url : "#{baseUrl}/js/vendor/tiny_mce/tinymce.min.js",
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
      toolbar: "formatselect | fontselect | bold italic underline forecolor | bullist numlist outdent indent | link unlink image | blockquote wrapAsCode | code",
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

    ed.on('SaveImage', @imageAdded)
    ed.on('ShowCodeMirror', @showCodeEditor)
    ed.on('SaveCodeMirror', @saveCodeEditor)

  imageAdded: (e) =>
    # Intended to run after the "image" plugin is used so that static urls are set
    # correctly in the Visual editor immediately after command use.
    @rewriteLinksFromStatic(e.target)

  showCodeEditor: (codeEditor) =>
    # Called with the CodeMirror Editor is displayed to convert links to show satic prefix.
    content = rewriteStaticLinks(codeEditor.getValue(), @base_asset_url, '/static/')
    codeEditor.setValue(content)

  saveCodeEditor: (codeEditor) =>
    # Called when the CodeMirror Editor is saved to convert links back to the full form.
    content = rewriteStaticLinks(codeEditor.getValue(), '/static/', @base_asset_url)
    codeEditor.setValue(content)

  initInstanceCallback: (visualEditor) =>
    @rewriteLinksFromStatic(visualEditor)
    @focusVisualEditor(visualEditor)

  rewriteLinksFromStatic: (visualEditor) =>
    visualEditor.setContent(rewriteStaticLinks(visualEditor.getContent({no_events: 1}), '/static/', @base_asset_url))

  focusVisualEditor: (visualEditor) =>
    visualEditor.focus()

  getVisualEditor: () ->
    ###
    Returns the instance of TinyMCE.
    This is different from the textarea that exists in the HTML template (@tiny_mce_textarea.

    Pulled out as a helper method for unit test.
    ###
    return @visualEditor

  save: ->
    visualEditor = @getVisualEditor()
    if visualEditor.isDirty()
      text = rewriteStaticLinks(visualEditor.getContent({no_events: 1}), @base_asset_url, '/static/')
    data: text
