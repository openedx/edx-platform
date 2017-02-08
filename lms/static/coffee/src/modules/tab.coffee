class @Tab
  constructor: (@id, @items) ->
    @el = $("#tab_#{id}")
    @render()

  $: (selector) ->
    $(selector, @el)

  render: ->
    $.each @items, (index, item) =>
      tab = $('<a>').attr(href: "##{@tabId(index)}").html(item.title)
      @$('.navigation').append($('<li>').append(tab))
      @el.append($('<section>').attr(id: @tabId(index)))
    @el.tabs
      show: @onShow

  onShow: (element, ui) =>
    @$('section.ui-tabs-hide').html('')
    @$("##{@tabId(ui.index)}").html(@items[ui.index]['content'])
    @el.trigger 'contentChanged'

  tabId: (index) ->
    "tab-#{@id}-#{index}"
