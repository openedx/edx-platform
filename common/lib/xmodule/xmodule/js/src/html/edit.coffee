class @HTMLEditingDescriptor

  constructor: (element) ->
    @element = element
    @base_asset_url = @element.find("#editor-tab").data('base-asset-url')
    @editor_choice = @element.find("#editor-tab").data('editor')
    if @base_asset_url == undefined
      @base_asset_url = null

    # We always create the "raw editor" so we can get the text out of it if necessary on save.
    @advanced_editor = CodeMirror.fromTextArea($(".edit-box", @element)[0], {
        mode: "text/html"
        lineNumbers: true
        lineWrapping: true
    })

    if @editor_choice == 'visual'
      @$advancedEditorWrapper = $(@advanced_editor.getWrapperElement())
      @$advancedEditorWrapper.addClass('is-inactive')
      # Create an array of all content CSS links to use in and pass to Tiny MCE.
      # We create this dynamically in order to support hashed files from our Django pipeline.
      # CSS files that are to be used by Tiny MCE should contain the string "tinymce" so
      # they can be found by the search below.
      # We filter for only those files that are "content" files (as opposed to "skin" files).
      tiny_mce_css_links = []
      $("link[rel=stylesheet][href*='tinymce']").filter("[href*='content']").each ->
          tiny_mce_css_links.push $(this).attr("href")
          return

  #   This is a workaround for the fact that tinyMCE's baseURL property is not getting correctly set on AWS
  #   instances (like sandbox). It is not necessary to explicitly set baseURL when running locally.
      tinyMCE.baseURL = "#{baseUrl}/js/vendor/tinymce/js/tinymce"
  #   This is necessary for the LMS bulk e-mail acceptance test. In that particular scenario,
  #   tinyMCE incorrectly decides that the suffix should be "", which means it fails to load files.
      tinyMCE.suffix = ".min"
      @tiny_mce_textarea = $(".tiny-mce", @element).tinymce({
        script_url : "#{baseUrl}/js/vendor/tinymce/js/tinymce/tinymce.full.min.js",
        theme : "modern",
        skin: 'studio-tmce4',
        schema: "html5",
        # Necessary to preserve relative URLs to our images.
        convert_urls : false,
        content_css : tiny_mce_css_links.join(", "),
        formats : {
          # tinyMCE does block level for code by default
          code: {inline: 'code'}
        },
        # Disable visual aid on borderless table.
        visual: false,
        plugins: "textcolor, link, image, codemirror",
        codemirror: {
          path: "#{baseUrl}/js/vendor"
        },
        image_advtab: true,
        # We may want to add "styleselect" when we collect all styles used throughout the LMS
        toolbar: "formatselect | fontselect | bold italic underline forecolor wrapAsCode | bullist numlist outdent indent blockquote | link unlink image | code",
        block_formats: "Paragraph=p;Preformatted=pre;Heading 1=h1;Heading 2=h2;Heading 3=h3",
        width: '100%',
        height: '400px',
        menubar: false,
        statusbar: false,
        
        # Necessary to avoid stripping of style tags.
        valid_children : "+body[style]",

        # Allow any elements to be used, e.g. link, script, math
        valid_elements: "*[*]",
        extended_valid_elements: "*[*]",
        invalid_elements: "",
        
        setup: @setupTinyMCE,
        # Cannot get access to tinyMCE Editor instance (for focusing) until after it is rendered.
        # The tinyMCE callback passes in the editor as a parameter.
        init_instance_callback: @initInstanceCallback
      })

  setupTinyMCE: (ed) =>
    ed.addButton('wrapAsCode', {
      title : 'Code block',
      image : "#{baseUrl}/images/ico-tinymce-code.png",
      onclick : () ->
        ed.formatter.toggle('code')
    })

    @visualEditor = ed

    # These events were added to the plugin code as the TinyMCE PluginManager
    # does not fire any events when plugins are opened or closed.
    ed.on('SaveImage', @saveImage)
    ed.on('EditImage', @editImage)
    ed.on('SaveLink', @saveLink)
    ed.on('EditLink', @editLink)
    ed.on('ShowCodeEditor', @showCodeEditor)
    ed.on('SaveCodeEditor', @saveCodeEditor)

  editImage: (data) =>
    # Called when the image plugin will be shown. Input arg is the JSON version of the image data.
    if data['src']
      data['src'] = rewriteStaticLinks(data['src'], @base_asset_url, '/static/')

  saveImage: (data) =>
    # Called when the image plugin is saved. Input arg is the JSON version of the image data.
    if data['src']
      data['src'] = rewriteStaticLinks(data['src'], '/static/', @base_asset_url)

  editLink: (data) =>
    # Called when the link plugin will be shown. Input arg is the JSON version of the link data.
    if data['href']
      data['href'] = rewriteStaticLinks(data['href'], @base_asset_url, '/static/')

  saveLink: (data) =>
    # Called when the link plugin is saved. Input arg is the JSON version of the link data.
    if data['href']
      data['href'] = rewriteStaticLinks(data['href'], '/static/', @base_asset_url)

  showCodeEditor: (source) =>
    # Called when the CodeMirror Editor is displayed to convert links to show static prefix.
    # The input argument is a dict with the text content.
    content = rewriteStaticLinks(source.content, @base_asset_url, '/static/')
    source.content = content

  saveCodeEditor: (source) =>
    # Called when the CodeMirror Editor is saved to convert links back to the full form.
    # The input argument is a dict with the text content.
    content = rewriteStaticLinks(source.content, '/static/', @base_asset_url)
    source.content = content

  initInstanceCallback: (visualEditor) =>
    visualEditor.setContent(rewriteStaticLinks(visualEditor.getContent({no_events: 1}), '/static/', @base_asset_url))
    # Unfortunately, just setting visualEditor.isNortDirty = true is not enough to convince TinyMCE we
    # haven't dirtied the Editor. Store the raw content so we can compare it later.
    @starting_content = visualEditor.getContent({format:"raw", no_events: 1})
    visualEditor.focus()

  getVisualEditor: () ->
    ###
    Returns the instance of TinyMCE.

    Pulled out as a helper method for unit test.
    ###
    return @visualEditor

  save: ->
    text = undefined
    if @editor_choice == 'visual'
      visualEditor = @getVisualEditor()
      raw_content = visualEditor.getContent({format:"raw", no_events: 1})
      if @starting_content != raw_content
        text = rewriteStaticLinks(visualEditor.getContent({no_events: 1}), @base_asset_url, '/static/')

    if text == undefined
      text = @advanced_editor.getValue()

    data: text
