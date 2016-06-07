class @Histogram
  constructor: (@id, @rawData) ->
    @xTicks = []
    @yTicks = []
    @data = []
    @calculate()
    @render()

  calculate: ->
    for [score, count] in @rawData
      continue if score == null
      log_count = Math.log(count + 1)
      @data.push [score, log_count]
      @xTicks.push [score, score.toString()]
      @yTicks.push [log_count, count.toString()]

  render: ->
    $.plot $("#histogram_#{@id}"), [
      data: @data
      bars:
        show: true
        align: 'center'
        lineWidth: 0
        fill: 1.0
      color: "#b72121"
    ],
      xaxis:
        min: -1
        max: Math.max.apply Math, $.map(@xTicks, (data) -> data[0] + 1)
        ticks: @xTicks
        tickLength: 0
      yaxis:
        min: 0.0
        max: Math.max.apply Math, $.map(@yTicks, (data) -> data[0] * 1.1)
        ticks: @yTicks
        labelWidth: 50
