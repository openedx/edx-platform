class @TrackChanges
  reset_button_sel: '.reset-changes'
  tracked_feedback_sel: '.feedback-area.track-changes'
  submit_button_sel: '.submit-button'
  tracker: null

  constructor: (element) ->
    @el = element
    @reset_button = @$(@reset_button_sel)
    @submit_button = @$(@submit_button_sel)
    @tracked_feedback = @$(@tracked_feedback_sel)
    @reset_button.click @reset_changes
    @submit_button.click @stop_tracking_on_submit


  rebindTracker: () =>
    if @tracker?
      @tracker.stopTracking()
      delete @tracker
    @tracker = new ice.InlineChangeEditor({
      element: @tracked_feedback[0], #return DOM element from selector
      handleEvents: true,
      currentUser: { id: 1, name: 'Peer Feedback' }, #hardcoded current user
      # optional plugins
      plugins: [
        # Track content that is cut and pasted
        {
          name: 'IceCopyPastePlugin',
          settings: {
            # List of tags and attributes to preserve when cleaning a paste
            preserve: 'p,a[href],span[id,class],em,strong'
          }
        }
      ]
    })
    @tracker.startTracking()

  # locally scoped jquery. (scoped to the element)
  $: (selector) ->
    $(selector, @el)

  reset_changes: (event) =>
    event.preventDefault()
    @tracker.rejectAll()

  stop_tracking_on_submit: () =>
    @tracker.stopTracking()
