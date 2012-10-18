class @JavascriptLoader

  # Set of library functions that provide common interface for javascript loading
  # for all module types. All functionality provided by JavascriptLoader should take
  # place at module scope, i.e. don't run jQuery over entire page

  # executeModuleScripts:
  #   Scan the module ('el') for "script_placeholder"s, then:
  #     1) Fetch each script from server
  #     2) Explicitly attach the script to the <head> of document
  #     3) Explicitly wait for each script to be loaded
  #     4) Return to callback function when all scripts loaded
  @executeModuleScripts: (el, callback=null) ->

    placeholders = el.find(".script_placeholder")

    if placeholders.length == 0
      callback() if callback?
      return

    # TODO: Verify the execution order of multiple placeholders
    completed      = (false for i in [1..placeholders.length])
    callbackCalled = false

    # This is required for IE8 support.
    completionHandlerGeneratorIE = (index) =>
      return () ->
        if (this.readyState == 'complete' || this.readyState == 'loaded')
          #completionHandlerGenerator.call(self, index)()
          completionHandlerGenerator(index)()

    completionHandlerGenerator = (index) =>
      return () =>
        allComplete = true
        completed[index] = true
        for flag in completed
          if not flag
            allComplete = false
            break
        if allComplete and not callbackCalled
          callbackCalled = true
          callback() if callback?

    # Keep a map of what sources we're loaded from, and don't do it twice.
    loaded = {}
    placeholders.each (index, placeholder) ->
      # TODO: Check if the script already exists in DOM. If so, (1) copy it
      #         into memory; (2) delete the DOM script element; (3) reappend it.
      #       This would prevent memory bloat and save a network request.
      src = $(placeholder).attr("data-src")
      if src not of loaded
        loaded[src] = true
        s = document.createElement('script')
        s.setAttribute('src', src)
        s.setAttribute('type', "text/javascript")
  
        s.onload             = completionHandlerGenerator(index)

        # s.onload does not fire in IE8; this does.
        s.onreadystatechange = completionHandlerGeneratorIE(index)

        # Need to use the DOM elements directly or the scripts won't execute
        # properly.
        $('head')[0].appendChild(s)
      else
        # just call the completion callback directly, without reloading the file
        completionHandlerGenerator(index)()
      $(placeholder).remove()
        
      
