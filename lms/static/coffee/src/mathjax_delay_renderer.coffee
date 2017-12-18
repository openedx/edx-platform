getTime = ->
  new Date().getTime()

class @MathJaxDelayRenderer

  maxDelay: 3000
  mathjaxRunning: false
  elapsedTime: 0
  mathjaxDelay: 0
  mathjaxTimeout: undefined
  bufferId = "mathjax_delay_buffer"
  numBuffers = 0

  constructor: (params) ->
    params = params || {}
    @maxDelay = params["maxDelay"] || @maxDelay
    @bufferId = params["bufferId"] || (bufferId + numBuffers)
    numBuffers += 1
    @$buffer = $("<div>").attr("id", @bufferId).css("display", "none").appendTo($("body"))

  # render: (params) ->
  # params:
  #   elem: jquery element to be rendered
  #   text: text to be rendered & put into the element;
  #     if blank, then just render the current text in the element
  #   preprocessor: pre-process the text before rendering using MathJax
  #     if text is blank, it will pre-process the html in the element
  #   previewSetter: if provided, will pass text back to it instead of
  #     directly setting the element

  render: (params) ->

    elem = params["element"]
    previewSetter = params["previewSetter"]
    text = params["text"]
    if not text?
      text = $(elem).html()
    preprocessor = params["preprocessor"]

    if params["delay"] == false
      if preprocessor?
        text = preprocessor(text)
      $(elem).html(text)
      MathJax.Hub.Queue ["Typeset", MathJax.Hub, $(elem).attr("id")]
    else
      if @mathjaxTimeout
        window.clearTimeout(@mathjaxTimeout)
        @mathjaxTimeout = undefined
      delay = Math.min @elapsedTime + @mathjaxDelay, @maxDelay
      
      renderer = =>
        if @mathjaxRunning
          return
        prevTime = getTime()
        if preprocessor?
          text = preprocessor(text)
        @$buffer.html(text)
        curTime = getTime()
        @elapsedTime = curTime - prevTime
        if MathJax?
          prevTime = getTime()
          @mathjaxRunning = true
          MathJax.Hub.Queue ["Typeset", MathJax.Hub, @$buffer.attr("id")], =>
            @mathjaxRunning = false
            curTime = getTime()
            @mathjaxDelay = curTime - prevTime
            if previewSetter
              previewSetter($(@$buffer).html())
            else
              $(elem).html($(@$buffer).html())
        else
          @mathjaxDelay = 0
      @mathjaxTimeout = window.setTimeout(renderer, delay)
