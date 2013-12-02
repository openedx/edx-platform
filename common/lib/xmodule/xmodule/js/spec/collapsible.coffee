describe 'Collapsible', ->
  html = custom_labels = html_custom = el = undefined

  initialize = (template) =>
    setFixtures(template)
    el = $('.collapsible')
    Collapsible.setCollapsibles(el)

  disableFx = () =>
    $.fx.off = true

  enableFx = () =>
    $.fx.off = false

  beforeEach ->
    html = '''
    <section class="collapsible">
      <div class="shortform">
          shortform message
      </div>
      <div class="longform">
        <p>longform is visible</p>
      </div>
    </section>
    '''
    html_custom =  '''
    <section class="collapsible">
      <div class="shortform-custom" data-open-text="Show shortform-custom" data-close-text="Hide shortform-custom">
          shortform message
      </div>
      <div class="longform">
        <p>longform is visible</p>
      </div>
    </section>
    '''

  describe 'setCollapsibles', ->

    it 'Default container initialized correctly', ->
      initialize(html)

      expect(el.find('.shortform')).toContain '.full-top'
      expect(el.find('.shortform')).toContain '.full-bottom'
      expect(el.find('.longform')).toBeHidden()
      expect(el.find('.full')).toHandle('click')

    it 'Custom container initialized correctly', ->
      initialize(html_custom)

      expect(el.find('.shortform-custom')).toContain '.full-custom'
      expect(el.find('.full-custom')).toHaveText "Show shortform-custom"
      expect(el.find('.longform')).toBeHidden()
      expect(el.find('.full-custom')).toHandle('click')

  describe 'toggleFull', ->

    beforeEach ->
      disableFx()

    afterEach ->
      enableFx()

    it 'Default container', ->
      initialize(html)

      event = jQuery.Event('click', {
        target: el.find('.full').get(0)
      })

      assertChanges = (state='closed') =>
        anchors = el.find('.full')

        if state is 'closed'
          expect(el.find('.longform')).toBeHidden()
          expect(el).not.toHaveClass('open')
          text = "See full output"
        else
          expect(el.find('.longform')).toBeVisible()
          expect(el).toHaveClass('open')
          text = "Hide output"

        $.each anchors, (index, el) =>
          expect(el).toHaveText text

      Collapsible.toggleFull(event, "See full output", "Hide output")
      assertChanges('opened')
      Collapsible.toggleFull(event, "See full output", "Hide output")
      assertChanges('closed')

    it 'Custom container', ->
      initialize(html_custom)

      event = jQuery.Event('click', {
        target: el.find('.full-custom').get(0)
      })

      assertChanges = (state='closed') =>
        anchors = el.find('.full-custom')

        if state is 'closed'
          expect(el.find('.longform')).toBeHidden()
          expect(el).not.toHaveClass('open')
          text = "Show shortform-custom"
        else
          expect(el.find('.longform')).toBeVisible()
          expect(el).toHaveClass('open')
          text = "Hide shortform-custom"

        $.each anchors, (index, el) =>
          expect(el).toHaveText text

      Collapsible.toggleFull(event, "Show shortform-custom", "Hide shortform-custom")
      assertChanges('opened')
      Collapsible.toggleFull(event, "Show shortform-custom", "Hide shortform-custom")
      assertChanges('closed')
