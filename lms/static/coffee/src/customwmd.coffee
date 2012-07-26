$ ->

  if Markdown?
    mathRenderer = new MathJaxDelayRenderer()
    removeMath = (text) -> text

    replaceMath = (text) -> text

    updateMathJax = ->
      console.log "updating"
      #mathRenderer.render
      #  element: $("#wmd-preview")
      MathJax.Hub.Queue(["Typeset", MathJax.Hub, "wmd-preview"])


    converter = Markdown.getSanitizingConverter()
    editor = new Markdown.Editor(converter)
    converter.hooks.chain "preConversion", removeMath
    converter.hooks.chain "postConversion", replaceMath
    editor.hooks.chain "onPreviewRefresh", updateMathJax
    editor.run()
