(function() {

  describe('Histogram', function() {
    beforeEach(function() {
      return spyOn($, 'plot');
    });
    describe('constructor', function() {
      return it('instantiate the data arrays', function() {
        var histogram;
        histogram = new Histogram(1, []);
        expect(histogram.xTicks).toEqual([]);
        expect(histogram.yTicks).toEqual([]);
        return expect(histogram.data).toEqual([]);
      });
    });
    describe('calculate', function() {
      beforeEach(function() {
        return this.histogram = new Histogram(1, [[1, 1], [2, 2], [3, 3]]);
      });
      it('store the correct value for data', function() {
        return expect(this.histogram.data).toEqual([[1, Math.log(2)], [2, Math.log(3)], [3, Math.log(4)]]);
      });
      it('store the correct value for x ticks', function() {
        return expect(this.histogram.xTicks).toEqual([[1, '1'], [2, '2'], [3, '3']]);
      });
      return it('store the correct value for y ticks', function() {
        return expect(this.histogram.yTicks).toEqual;
      });
    });
    return describe('render', function() {
      return it('call flot with correct option', function() {
        new Histogram(1, [[1, 1], [2, 2], [3, 3]]);
        return expect($.plot).toHaveBeenCalledWith($("#histogram_1"), [
          {
            data: [[1, Math.log(2)], [2, Math.log(3)], [3, Math.log(4)]],
            bars: {
              show: true,
              align: 'center',
              lineWidth: 0,
              fill: 1.0
            },
            color: "#b72121"
          }
        ], {
          xaxis: {
            min: -1,
            max: 4,
            ticks: [[1, '1'], [2, '2'], [3, '3']],
            tickLength: 0
          },
          yaxis: {
            min: 0.0,
            max: Math.log(4) * 1.1,
            ticks: [[Math.log(2), '1'], [Math.log(3), '2'], [Math.log(4), '3']],
            labelWidth: 50
          }
        });
      });
    });
  });

}).call(this);
