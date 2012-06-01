class @Tab
  constructor: (@id, @items) ->
    @element = $("#tab_#{id}")
    @render()

  $: (selector) ->
    $(selector, @element)

  render: ->
    $.each @items, (index, item) =>
      tab = $('<a>').attr(href: "##{@tabId(index)}").html(item.title)
      @$('.navigation').append($('<li>').append(tab))
      @element.append($('<section>').attr(id: @tabId(index)))
    @element.tabs
      show: @onShow

  onShow: (element, ui) =>
    @$('section.ui-tabs-hide').html('')
    @$("##{@tabId(ui.index)}").html(@items[ui.index]['content'])
    @element.trigger 'contentChanged'

  tabId: (index) ->
    "tab-#{@id}-#{index}"
