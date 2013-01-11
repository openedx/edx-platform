class @HTMLEditingDescriptor
  constructor: (element) ->
    @element = element;
    text = $(".edit-box", @element)[0];
    replace_func = (elt) -> text.parentNode.replaceChild(elt, text)
    @advanced_editor = CodeMirror(replace_func, {
      value: text.innerHTML
      mode: "text/html"
      lineNumbers: true
      lineWrapping: true})
    $(@advanced_editor.getWrapperElement()).hide()

    @tiny_mce_textarea = $(".tiny-mce", @element).tinymce({
      script_url : '/static/js/vendor/tiny_mce/tiny_mce.js',
      theme : "advanced",
      schema: "html5",
      # TODO: we should share this CSS with studio (and LMS)
      content_css : "/static/css/tiny-mce.css",
      # We may want to add "styleselect" when we collect all styles used throughout the LMS
      theme_advanced_buttons1 : "formatselect,bold,italic,underline,bullist,numlist,outdent,indent,blockquote,link,unlink",
      theme_advanced_toolbar_location : "top",
      theme_advanced_toolbar_align : "left",
      theme_advanced_statusbar_location : "none",
      theme_advanced_resizing : true,
      theme_advanced_blockformats : "p,code,h2,h3,blockquote",
      width: '100%',
      height: '400px',
    })

    @showingVisualEditor = true
    @element.on('click', '.editor-tabs .tab', @onSwitchEditor)

  onSwitchEditor: (e)=>
    e.preventDefault();

    if not $(e.currentTarget).hasClass('current')
      $('.editor-tabs .current').removeClass('current')
      $(e.currentTarget).addClass('current')
      tinyMCE = @getVisualEditor()

      if $(e.currentTarget).attr('data-tab') is 'visual'
        $(@advanced_editor.getWrapperElement()).hide()
        tinyMCE.show()
        tinyMCE.setContent(@advanced_editor.getValue())
        # In order for tinyMCE.isDirty() to return true ONLY if edits have been made after setting the text,
        # both the startContent must be sync'ed up and the dirty flag set to false.
        tinyMCE.startContent = tinyMCE.getContent({format: "raw", no_events: 1});
        tinyMCE.isNotDirty = true
        @showingVisualEditor = true
      else
        tinyMCE.hide()
        @tiny_mce_textarea.hide()
        $(@advanced_editor.getWrapperElement()).show()
        if tinyMCE.isDirty()
          console.log('was dirty! setting text')
          @advanced_editor.setValue(tinyMCE.getContent({no_events: 1}))
          @advanced_editor.setCursor(0)
        @advanced_editor.refresh()
        @advanced_editor.focus()
        @showingVisualEditor = false

  getVisualEditor: ->
    ###
    Returns the instance of TinyMCE.
    This is different from the textarea that exists in the HTML template (@tiny_mce_textarea.
    ###
    return tinyMCE.get($('.tiny-mce', this.element).attr('id'))

  save: ->
    @element.off('click', '.editor-tabs .tab', @onSwitchEditor)
    text = @advanced_editor.getValue()
    tinyMCE = @getVisualEditor()
    if @showingVisualEditor and tinyMCE.isDirty()
      console.log('persist from visual editor')
      text = tinyMCE.getContent({no_events: 1})
    else
      console.log('persist from HTML editor')
    data: text
