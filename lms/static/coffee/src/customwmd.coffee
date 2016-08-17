# Mostly adapted from math.stackexchange.com: http://cdn.sstatic.net/js/mathjax-editing-new.js

class MathJaxProcessor

  MATHSPLIT = /// (
    \$\$?                          # normal inline or display delimiter
    | \\(?:begin|end)\{[a-z]*\*?\} # \begin{} \end{} style
    | \\[\\{}$]
    | [{}]
    | (?:\n\s*)+                   # only treat as math when there's single new line
    | @@\d+@@                      # delimiter similar to the one used internally
  ) ///i

  CODESPAN = ///
    (^|[^\\])       # match beginning or any previous character other than escape delimiter ('/')
    (`+)            # code span starts
    ([^\n]*?[^`\n]) # code content
    \2              # code span ends
    (?!`)
  ///gm

  constructor: (inlineMark, displayMark) ->
    @inlineMark = inlineMark || "$"
    @displayMark = displayMark || "$$"
    @math = null
    @blocks = null

  processMath: (start, last, preProcess) ->
    block = @blocks.slice(start, last + 1).join("").replace(/&/g, "&amp;")
                                                  .replace(/</g, "&lt;")
                                                  .replace(/>/g, "&gt;")
    if MathJax.Hub.Browser.isMSIE
      block = block.replace /(%[^\n]*)\n/g, "$1<br/>\n"
    @blocks[i] = "" for i in [start+1..last]
    @blocks[start] = "@@#{@math.length}@@"
    block = preProcess(block) if preProcess
    @math.push block

  removeMath: (text) ->

    text = text || ""
    @math = []
    start = end = last = null
    braces = 0

    hasCodeSpans = /`/.test text
    if hasCodeSpans
      text = text.replace(/~/g, "~T").replace CODESPAN, ($0) -> # replace dollar sign in code span temporarily
        $0.replace /\$/g, "~D"
      deTilde = (text) ->
        text.replace /~([TD])/g, ($0, $1) ->
          {T: "~", D: "$"}[$1]
    else
      deTilde = (text) -> text

    @blocks = _split(text.replace(/\r\n?/g, "\n"), MATHSPLIT)

    for current in [1...@blocks.length] by 2
      block = @blocks[current]
      if block.charAt(0) == "@"
        @blocks[current] = "@@#{@math.length}@@"
        @math.push block
      else if start
        if block == end
          if braces
            last = current
          else
            @processMath(start, current, deTilde)
            start = end = last = null
        else if block.match /\n.*\n/
          if last
            current = last
            @processMath(start, current, deTilde)
          start = end = last = null
          braces = 0
        else if block == "{"
          ++braces
        else if block == "}" and braces
          --braces
      else
        if block == @inlineMark or block == @displayMark
          start = current
          end = block
          braces = 0
        else if block.substr(1, 5) == "begin"
          start = current
          end = "\\end" + block.substr(6)
          braces = 0

    if last
      @processMath(start, last, deTilde)
      start = end = last = null

    deTilde(@blocks.join(""))

  @removeMathWrapper: (_this) ->
    (text) -> _this.removeMath(text)

  replaceMath: (text) ->
    text = text.replace /@@(\d+)@@/g, ($0, $1) => @math[$1]
    @math = null
    text

  @replaceMathWrapper: (_this) ->
    (text) -> _this.replaceMath(text)

if Markdown?

  Markdown.getMathCompatibleConverter = (postProcessor) ->
    postProcessor ||= ((text) -> text)
    converter = Markdown.getSanitizingConverter()
    if MathJax?
      processor = new MathJaxProcessor()
      converter.hooks.chain "preConversion", MathJaxProcessor.removeMathWrapper(processor)
      converter.hooks.chain "postConversion", (text) ->
        postProcessor(MathJaxProcessor.replaceMathWrapper(processor)(text))
    converter

  Markdown.makeWmdEditor = (elem, appended_id, imageUploadUrl, postProcessor) ->
    $elem = $(elem)
    if not $elem.length
      console.log "warning: elem for makeWmdEditor doesn't exist"
      return
    if not $elem.find(".wmd-panel").length
      initialText = $elem.html()
      $elem.empty()
      _append = appended_id || ""
      wmdInputId = "wmd-input#{_append}"
      $wmdPreviewContainer = $("<div>").addClass("wmd-preview-container").attr("aria-label", "HTML preview of post")
          .append($("<div>").addClass("wmd-preview-label").text(gettext("Preview")))
          .append($("<div>").attr("id", "wmd-preview#{_append}").addClass("wmd-panel wmd-preview"))
      $wmdPanel = $("<div>").addClass("wmd-panel")
                 .append($("<div>").attr("id", "wmd-button-bar#{_append}"))
                 .append($("<label>").addClass("sr").attr("for", wmdInputId).text(gettext("Post body")))
                 .append($("<textarea>").addClass("wmd-input").attr("id", wmdInputId).html(initialText))
                 .append($wmdPreviewContainer)
      $elem.append($wmdPanel)

    converter = Markdown.getMathCompatibleConverter(postProcessor)

    ajaxFileUpload = (imageUploadUrl, input, startUploadHandler) ->
      $("#loading").ajaxStart(-> $(this).show()).ajaxComplete(-> $(this).hide())
      $("#upload").ajaxStart(-> $(this).hide()).ajaxComplete(-> $(this).show())
      $.ajaxFileUpload
        url: imageUploadUrl
        secureuri: false
        fileElementId: 'file-upload'
        dataType: 'json'
        success: (data, status) ->
          fileURL = data['result']['file_url']
          error = data['result']['error']
          if error != ''
            alert error
            if startUploadHandler
              $('#file-upload').unbind('change').change(startUploadHandler)
            console.log error
          else
            $(input).attr('value', fileURL)
        error: (data, status, e) ->
          alert(e)
          if startUploadHandler
            $('#file-upload').unbind('change').change(startUploadHandler)

    imageUploadHandler = (elem, input) ->
      ajaxFileUpload(imageUploadUrl, input, imageUploadHandler)

    editor = new Markdown.Editor(
      converter,
      appended_id, # idPostfix
      null, # help handler
      imageUploadHandler
    )
    delayRenderer = new MathJaxDelayRenderer()
    editor.hooks.chain "onPreviewPush", (text, previewSet) ->
      delayRenderer.render
        text: text
        previewSetter: previewSet
    editor.run()
    editor
