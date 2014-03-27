(function (require) {
require(
['video/00_sjson.js'],
function (Sjson) {
    describe('Sjson', function () {
        var data = jasmine.stubbedCaption,
            sjson;

        beforeEach(function() {
            sjson = new Sjson(data);
        });

        it ('returns captions', function () {
            expect(sjson.getCaptions()).toEqual(data.text);
        });

        it ('returns start times', function () {
            expect(sjson.getStartTimes()).toEqual(data.start);
        });

        it ('returns correct length', function () {
            expect(sjson.getSize()).toEqual(data.text.length);
        });

        it('search returns a correct caption index', function () {
            expect(sjson.search(0)).toEqual(-1);
            expect(sjson.search(3120)).toEqual(1);
            expect(sjson.search(6270)).toEqual(2);
            expect(sjson.search(8490)).toEqual(2);
            expect(sjson.search(21620)).toEqual(4);
            expect(sjson.search(24920)).toEqual(5);
        });
    });
});
}(RequireJS.require));
