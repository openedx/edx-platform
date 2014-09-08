@XBlock =
  Runtime: {}

  ###
  Initialize the javascript for a single xblock element, and for all of it's
  xblock children that match requestToken. If requestToken is omitted, use the
  data-request-token attribute from element, or use the request-tokens specified on
  the children themselves.
  ###
  initializeBlock: (element, requestToken) ->
    $element = $(element)
    requestToken = requestToken or $element.data('request-token')
    children = @initializeBlocks($element, requestToken)
    runtime = $element.data("runtime-class")
    version = $element.data("runtime-version")
    initFnName = $element.data("init")
    $element.prop('xblock_children', children)
    if runtime? and version? and initFnName?
      runtime = new window[runtime]["v#{version}"]
      initFn = window[initFnName]
      if initFn.length > 2
        initargs = $(".xblock_json_init_args", element)
        if initargs.length == 0
          console.log("Warning: XBlock expects data parameters")
        data = JSON.parse(initargs.text())
        block = initFn(runtime, element, data) ? {}
      else
        block = initFn(runtime, element) ? {}
      block.runtime = runtime
    else
      elementTag = $('<div>').append($element.clone()).html();
      console.log("Block #{elementTag} is missing data-runtime, data-runtime-version or data-init, and can't be initialized")
      block = {}

    block.element = element
    block.name = $element.data("name")

    $element.trigger("xblock-initialized")
    $element.data("initialized", true)
    $element.addClass("xblock-initialized")
    block

  ###
  Initialize all XBlocks inside element that were rendered with requestToken.
  If requestToken is omitted, and element has a 'data-request-token' attribute, use that.
  If neither is available, then use the request tokens of the immediateDescendent xblocks.
  ###
  initializeBlocks: (element, requestToken) ->
    requestToken = requestToken or $(element).data('request-token')
    if requestToken
      selector = ".xblock[data-request-token='#{requestToken}']"
    else
      selector = ".xblock"
    $(element).immediateDescendents(selector).map((idx, elem) =>
      @initializeBlock(elem, requestToken)
    ).toArray()
