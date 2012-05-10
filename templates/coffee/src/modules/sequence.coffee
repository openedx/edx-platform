class window.Sequence
  constructor: (@id, @elements, @tag, position) ->
    @buildNavigation()
    @bind()
    @render position

  bind: ->
    $('#sequence-list a').click @goto
    $('#seq_content').change @toggleArrows

  buildNavigation: ->
    $.each @elements, (index, item) ->
      link = $('<a>').attr class: "seq_#{item.type}_inactive", 'data-element': index + 1
      title = $('<p>').html(item.title)
      list_item = $('<li>').append(link.append(title))
      $('#sequence-list').append list_item

  toggleArrows: =>
    $('.sequence-nav-buttons a').unbind('click')

    if @position == 1
      $('.sequence-nav-buttons .prev a').addClass('disabled')
    else
      $('.sequence-nav-buttons .prev a').removeClass('disabled').click(@previous)

    if @position == @elements.length
      $('.sequence-nav-buttons .next a').addClass('disabled')
    else
      $('.sequence-nav-buttons .next a').removeClass('disabled').click(@next)

  render: (new_position) ->
    if @position != undefined
      @mark_visited @position
      $.post "/modx/#{@tag}/#{@id}/goto_position", position: new_position

    if @position != new_position
      @mark_active new_position
      $('#seq_content').html eval(@elements[new_position - 1].content)

      MathJax.Hub.Queue(["Typeset",MathJax.Hub])
      @position = new_position
      $('#seq_content').trigger 'contentChanged'

  goto: (event) =>
    event.preventDefault()
    new_position = $(event.target).data('element')
    log_event("seq_goto", old: @position, new: new_position, id: @id)
    @render new_position

  next: (event) =>
    event.preventDefault()
    new_position = @position + 1
    log_event("seq_next", old: @position, new: new_position, id: @id)
    @render new_position

  previous: (event) =>
    event.preventDefault()
    new_position = @position - 1
    log_event("seq_prev", old: @position, new: new_position, id: @id)
    @render new_position

  link_for: (position) ->
    $("#sequence-list a[data-element=#{position}]")

  mark_visited: (position) ->
    @link_for(position).attr class: "seq_#{@elements[position - 1].type}_visited"

  mark_active: (position) ->
    @link_for(position).attr class: "seq_#{@elements[position - 1].type}_active"
