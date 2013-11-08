@XModule = {}

@XBlockToXModuleShim = (runtime, element) ->
  ###
  Load a single module (either an edit module or a display module)
  from the supplied element, which should have a data-type attribute
  specifying the class to load
  ###
  moduleType = $(element).data('type')
  if moduleType == 'None'
    return

  try
    module = new window[moduleType](element)
    if $(element).hasClass('xmodule_edit')
      $(document).trigger('XModule.loaded.edit', [element, module])

    if $(element).hasClass('xmodule_display')
      $(document).trigger('XModule.loaded.display', [element, module])

    return module

  catch error
    if window.console and console.log
      console.error "Unable to load #{moduleType}: #{error.message}"
    else
      throw error


class @XModule.Descriptor

  ###
  Register a callback method to be called when the state of this
  descriptor is updated. The callback will be passed the results
  of calling the save method on this descriptor.
  ###
  onUpdate: (callback) ->
    if ! @callbacks?
      @callbacks = []

    @callbacks.push(callback)

  ###
  Notify registered callbacks that the state of this descriptor has changed
  ###
  update: =>
    data = @save()
    callback(data) for callback in @callbacks

  ###
  Bind the module to an element. This may be called multiple times,
  if the element content has changed and so the module needs to be rebound

  @method: constructor
  @param {html element} the .xmodule_edit section containing all of the descriptor content
  ###
  constructor: (@element) -> return

  ###
  Return the current state of the descriptor (to be written to the module store)

  @method: save
  @returns {object} An object containing children and data attributes (both optional).
                    The contents of the attributes will be saved to the server
  ###
  save: -> return {}
