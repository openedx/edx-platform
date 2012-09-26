@XModule =
  ###
  Load a single module (either an edit module or a display module)
  from the supplied element, which should have a data-type attribute
  specifying the class to load
  ###
  loadModule: (element) ->
    moduleType = $(element).data('type')
    if moduleType == 'None'
      return

    try
      $(element).data('module', new window[moduleType](element))
      $(document).trigger('XModule.loaded', [element])
    catch error
      console.error "Unable to load #{moduleType}: #{error.message}" if console

  ###
  Load all modules on the page of the specified type.
  If container is provided, only load modules inside that element
  Type is one of 'display' or 'edit'
  ###
  loadModules: (container) ->
    selector = ".xmodule_edit, .xmodule_display"

    if container?
      modules = $(container).find(selector)
    else
      modules = $(selector)

    modules.each (idx, element) -> XModule.loadModule element
