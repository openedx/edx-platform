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

    @tiny_mce = $(".tiny-mce", @element).tinymce({
      script_url : '/static/js/vendor/tiny_mce/tiny_mce.js',
      theme : "advanced",
      #skin: 'studio',

      # we may want to add "styleselect" when we collect all styles used throughout the lms
      theme_advanced_buttons1 : "formatselect,bold,italic,underline,studio.asset,bullist,numlist,outdent,indent,blockquote,link,unlink",
      theme_advanced_toolbar_location : "top",
      theme_advanced_toolbar_align : "left",
      theme_advanced_statusbar_location : "none",
      theme_advanced_resizing : true,
      theme_advanced_blockformats : "p,code,h2,h3,blockquote",
      width: '100%',
      height: '400px'
    })
#    @tiny_mce.focus()
#    /tinyMCE.activeEditor.setContent(text, {format : 'raw'});
#    @tiny = tinyMCE.get($('.tiny-mce', this.element).attr('id'))
#    @tiny.setContent(@edit_box.getValue(), {format : 'raw'});
#    @tiny_mce.html(@edit_box.getValue())
    @visual_editor = tinyMCE.get($('.tiny-mce', this.element).attr('id'))

  save: ->
    data: @advanced_editor.getValue()
