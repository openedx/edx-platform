describe 'Histogram', ->
  beforeEach ->
    spyOn $, 'plot'

  describe 'constructor', ->
    it 'instantiate the data arrays', ->
      histogram = new Histogram 1, []
      expect(histogram.xTicks).toEqual []
      expect(histogram.yTicks).toEqual []
      expect(histogram.data).toEqual []

  describe 'calculate', ->
    beforeEach ->
      @histogram = new Histogram(1, [[null, 1], [1, 1], [2, 2], [3, 3]])

    it 'store the correct value for data', ->
      expect(@histogram.data).toEqual [[1, Math.log(2)], [2, Math.log(3)], [3, Math.log(4)]]

    it 'store the correct value for x ticks', ->
      expect(@histogram.xTicks).toEqual [[1, '1'], [2, '2'], [3, '3']]

    it 'store the correct value for y ticks', ->
      expect(@histogram.yTicks).toEqual

  describe 'render', ->
    it 'call flot with correct option', ->
      new Histogram(1, [[1, 1], [2, 2], [3, 3]])

      firstArg = $.plot.calls.mostRecent().args[0]
      secondArg = $.plot.calls.mostRecent().args[1]
      thirdArg = $.plot.calls.mostRecent().args[2]

      expect(firstArg.selector).toEqual($("#histogram_1").selector)
      expect(secondArg).toEqual([
        data: [[1, Math.log(2)], [2, Math.log(3)], [3, Math.log(4)]]
        bars:
          show: true
          align: 'center'
          lineWidth: 0
          fill: 1.0
        color: "#b72121"
      ])
      expect(thirdArg).toEqual(
        xaxis:
          min: -1
          max: 4
          ticks: [[1, '1'], [2, '2'], [3, '3']]
          tickLength: 0
        yaxis:
          min: 0.0
          max: Math.log(4) * 1.1
          ticks: [[Math.log(2), '1'], [Math.log(3), '2'], [Math.log(4), '3']]
          labelWidth: 50
      )
