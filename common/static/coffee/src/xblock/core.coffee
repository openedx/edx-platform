@XBlock =
  runtime: {}

  initializeBlock: (element) ->
    $element = $(element)
    children = @initializeBlocks($element)
    version = $element.data("runtime-version")
    initFnName = $element.data("init")
    if version? and initFnName?
      runtime = @runtime["v#{version}"](element, children)
      initFn = window[initFnName]
      block = initFn(runtime, element) ? {}
    else
      elementTag = $('<div>').append($element.clone()).html();
      console.log("Block #{elementTag} is missing data-runtime-version or data-init, and can't be initialized")
      block = {}

    block.element = element
    block.name = $element.data("name")

    block

  initializeBlocks: (element) ->
    $(element).immediateDescendents(".xblock").map((idx, elem) =>
      @initializeBlock elem
    ).toArray()
