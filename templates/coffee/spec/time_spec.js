(function() {

  describe('Time', function() {
    describe('format', function() {
      describe('with duration more than or equal to 1 hour', function() {
        return it('return a correct time format', function() {
          expect(Time.format(3600)).toEqual('1:00:00');
          return expect(Time.format(7272)).toEqual('2:01:12');
        });
      });
      return describe('with duration less than 1 hour', function() {
        return it('return a correct time format', function() {
          expect(Time.format(1)).toEqual('0:01');
          expect(Time.format(61)).toEqual('1:01');
          return expect(Time.format(3599)).toEqual('59:59');
        });
      });
    });
    return describe('convert', function() {
      return it('return a correct time based on speed modifier', function() {
        expect(Time.convert(0, 1, 1.5)).toEqual('0.000');
        expect(Time.convert(100, 1, 1.5)).toEqual('66.667');
        return expect(Time.convert(100, 1.5, 1)).toEqual('150.000');
      });
    });
  });

}).call(this);
